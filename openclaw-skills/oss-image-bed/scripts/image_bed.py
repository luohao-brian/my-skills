#!/usr/bin/env python3
"""Upload-only temporary file links for OSS and TOS."""
import argparse
import datetime as dt
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
import uuid
from urllib.parse import urlsplit, urlunsplit

PREFIX = 'image_bed_temp/'
RULE_ID = 'oss-image-bed-temp-expire'


class ConfigError(Exception):
    pass


def value(item):
    return getattr(item, 'value', item)


def config(env):
    required = ['PROVIDER', 'ACCESS_KEY', 'SECRET_KEY', 'BUCKET', 'REGION']
    missing = ['IMAGE_BED_' + key for key in required if not env.get('IMAGE_BED_' + key, '').strip()]
    if missing:
        raise ConfigError('Missing environment variables: ' + ', '.join(missing))
    result = {key.lower(): env['IMAGE_BED_' + key].strip() for key in required}
    aliases = {'tos': 'tos', 'volcengine': 'tos', 'oss': 'oss', 'aliyun': 'oss', 'ali': 'oss'}
    result['provider'] = aliases.get(result['provider'].lower())
    if not result['provider']:
        raise ConfigError('IMAGE_BED_PROVIDER must be tos or oss (volcengine/aliyun/ali accepted).')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]', result['bucket']):
        raise ConfigError('IMAGE_BED_BUCKET must be a bucket name.')
    if not re.fullmatch(r'[a-z][a-z0-9-]+', result['region']):
        raise ConfigError('Invalid IMAGE_BED_REGION.')
    provider, region = result['provider'], result['region']
    default = f'https://tos-{region}.volces.com' if provider == 'tos' else f'https://oss-{region}.aliyuncs.com'
    endpoint = env.get('IMAGE_BED_ENDPOINT', default).strip()
    if '://' not in endpoint:
        endpoint = 'https://' + endpoint
    parsed = urlsplit(endpoint)
    suffix = '.volces.com' if provider == 'tos' else '.aliyuncs.com'
    if (parsed.scheme != 'https' or not parsed.hostname or not parsed.hostname.endswith(suffix)
            or parsed.username or parsed.password or parsed.port or parsed.path not in ('', '/')
            or parsed.query or parsed.fragment or not parsed.hostname.startswith(provider + '-')):
        raise ConfigError('IMAGE_BED_ENDPOINT must be an official HTTPS object storage endpoint.')
    result['endpoint'] = endpoint.rstrip('/')
    domain = env.get('IMAGE_BED_CUSTOM_DOMAIN', '').strip()
    if domain:
        parsed = urlsplit(domain)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                or parsed.port or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
            raise ConfigError('IMAGE_BED_CUSTOM_DOMAIN must be an HTTPS origin without a path.')
    result['custom_domain'] = domain.rstrip('/')
    return result


def make_key(agent, filename):
    agent = re.sub(r'[^A-Za-z0-9_-]+', '-', agent).strip('-_')[:48] or 'agent'
    suffix = Path(filename).suffix.lower()
    if not re.fullmatch(r'\.[a-z0-9]{1,16}', suffix):
        suffix = ''
    timestamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    return f'{PREFIX}{agent}-{timestamp}-{uuid.uuid4().hex}{suffix}'


def compatible(rule):
    expiration = getattr(rule, 'expiration', None)
    return (rule.prefix == PREFIX and value(rule.status) == 'Enabled'
            and expiration is not None and expiration.days == 1
            and not any(getattr(expiration, n, None) for n in ['date', 'created_before_date'])
            and not any(getattr(rule, n, None) for n in [
                'tags', 'tagging', 'filter', 'transitions', 'storage_transitions',
                'access_time_transitions', 'atime_base']))


class Storage:
    def __init__(self, cfg):
        self.cfg = cfg
        self.tos = cfg['provider'] == 'tos'
        if self.tos:
            import tos
            self.sdk = tos
            self.client = tos.TosClientV2(cfg['access_key'], cfg['secret_key'],
                                        cfg['endpoint'], cfg['region'], connection_time=10, socket_timeout=30)
        else:
            import oss2
            self.sdk = oss2
            auth = oss2.AuthV4(cfg['access_key'], cfg['secret_key'])
            self.client = oss2.Bucket(auth, cfg['endpoint'], cfg['bucket'], region=cfg['region'], connect_timeout=30)

    def rules(self):
        try:
            result = (self.client.get_bucket_lifecycle(self.cfg['bucket']) if self.tos
                      else self.client.get_bucket_lifecycle())
            return result.rules
        except Exception as exc:
            if getattr(exc, 'code', None) == 'NoSuchLifecycleConfiguration':
                return []
            raise

    def check_version(self):
        state = (self.client.get_bucket_version(self.cfg['bucket']).status if self.tos
                 else self.client.get_bucket_versioning().status)
        if value(state) not in (None, '', 'Unknown'):
            raise ConfigError('Use a bucket with versioning never enabled; current/historical objects must be fully cleaned.')

    def check_lifecycle(self):
        if not any(compatible(r) for r in self.rules()):
            raise ConfigError('Missing compatible image_bed_temp/ 1-day cleanup rule. Run setup-lifecycle once before uploads.')

    def setup(self):
        self.check_version()
        rules = self.rules()
        if any(compatible(r) for r in rules):
            return 'already_configured'
        if rules:
            raise ConfigError('Existing lifecycle configuration: administrator must merge a prefix-only 1-day rule; no rules were changed.')
        if self.tos:
            model = self.sdk.models2
            rule = model.BucketLifeCycleRule(id=RULE_ID, prefix=PREFIX,
                                            status=self.sdk.enum.StatusType.Status_Enable,
                                            expiration=model.BucketLifeCycleExpiration(days=1))
            self.client.put_bucket_lifecycle(self.cfg['bucket'], [rule])
        else:
            model = self.sdk.models
            rule = model.LifecycleRule(RULE_ID, PREFIX, expiration=model.LifecycleExpiration(days=1))
            self.client.put_bucket_lifecycle(model.BucketLifecycle([rule]))
        self.check_lifecycle()
        return 'configured'

    def put(self, path, key, content_type):
        if self.tos:
            self.client.put_object_from_file(self.cfg['bucket'], key, str(path),
                content_type=content_type, content_disposition='inline', cache_control='private, no-store',
                acl=self.sdk.enum.ACLType.ACL_Private, storage_class=self.sdk.enum.StorageClassType.Storage_Class_Standard,
                forbid_overwrite=True)
        else:
            self.client.put_object_from_file(key, str(path), headers={
                'Content-Type': content_type, 'Content-Disposition': 'inline',
                'Cache-Control': 'private, no-store', 'x-oss-object-acl': 'private',
                'x-oss-storage-class': 'Standard', 'x-oss-forbid-overwrite': 'true'})

    def sign(self, key, seconds):
        domain = self.cfg['custom_domain']
        if self.tos:
            return self.client.pre_signed_url(self.sdk.enum.HttpMethodType.Http_Method_Get,
                self.cfg['bucket'], key, expires=seconds,
                alternative_endpoint=domain or None, is_custom_domain=bool(domain)).signed_url
        client = self.client
        if domain:
            client = self.sdk.Bucket(self.client.auth, domain, self.cfg['bucket'],
                                     region=self.cfg['region'], is_cname=True)
        return client.sign_url('GET', key, seconds)


def ensure_private(url):
    import requests
    parsed = urlsplit(url)
    unsigned = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
    with requests.get(unsigned, headers={'Range': 'bytes=0-0'}, stream=True,
                      timeout=(10, 30), allow_redirects=False) as response:
        if response.status_code != 403:
            raise ConfigError('Unsigned access did not return 403; verify private bucket/policy/domain configuration. Uploaded object awaits lifecycle cleanup.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('setup-lifecycle', help='One-time setup on a bucket without existing lifecycle rules.')
    upload = sub.add_parser('upload', help='Upload one file and return a temporary GET URL.')
    upload.add_argument('file', type=Path)
    upload.add_argument('--agent-name', required=True)
    upload.add_argument('--expires-in', type=int, default=3600, help='URL lifetime in seconds, 1–86400 (default 3600).')
    args = parser.parse_args(argv)
    key = None
    try:
        if args.command == 'upload':
            if not 1 <= args.expires_in <= 86400:
                raise ConfigError('--expires-in must be an integer from 1 to 86400 seconds.')
            if not args.file.is_file():
                raise ConfigError('Input must be an existing regular file.')
        cfg = config(os.environ)
        storage = Storage(cfg)
        if args.command == 'setup-lifecycle':
            result = {'ok': True, 'lifecycle': storage.setup(), 'prefix': PREFIX, 'expiration_days': 1}
        else:
            storage.check_version()
            storage.check_lifecycle()
            key = make_key(args.agent_name, args.file.name)
            content_type = mimetypes.guess_type(args.file.name)[0] or 'application/octet-stream'
            if content_type.startswith('text/'):
                content_type += '; charset=utf-8'
            storage.put(args.file, key, content_type)
            signed_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
            url = storage.sign(key, args.expires_in)
            ensure_private(url)
            result = {'ok': True, 'provider': cfg['provider'], 'bucket': cfg['bucket'],
                'object_key': key, 'url': url, 'expires_in': args.expires_in,
                'expires_at': (signed_at + dt.timedelta(seconds=args.expires_in)).isoformat().replace('+00:00', 'Z'),
                'size_bytes': args.file.stat().st_size, 'content_type': content_type,
                'cleanup': {'expiration_days': 1, 'deletion': 'asynchronous'}}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        error = {'ok': False, 'error': type(exc).__name__}
        if isinstance(exc, ConfigError):
            error['message'] = str(exc)
        elif isinstance(exc, ImportError):
            error['message'] = 'Install dependencies from requirements.txt in the executing Python environment.'
        else:
            code = getattr(exc, 'code', None)
            if code and re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', str(code)):
                error['code'] = code
            error['message'] = 'Storage request failed; check endpoint, credentials, permissions and connectivity.'
        if key:
            error['object_key'] = key
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
