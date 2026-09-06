"""Offline checks for upload boundaries and lifecycle safety."""
import concurrent.futures
import contextlib
import io
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import image_bed as bed


class ImageBedTests(unittest.TestCase):
    def test_both_official_sdks_sign_urls_with_requested_lifetime(self):
        for provider in ['tos', 'oss']:
            cfg = bed.config({'IMAGE_BED_' + k: v for k, v in {
                'PROVIDER': provider, 'ACCESS_KEY': 'test-access-key', 'SECRET_KEY': 'test-secret',
                'BUCKET': 'example-bucket', 'REGION': 'cn-beijing'}.items()})
            storage = bed.Storage(cfg)
            for seconds in [3600, 86400]:
                url = storage.sign(bed.PREFIX + 'agent-test.html', seconds)
                parsed = urlsplit(url)
                query = {k.lower(): v for k, v in parse_qs(parsed.query).items()}
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(query['x-tos-expires' if provider == 'tos' else 'x-oss-expires'], [str(seconds)])
                self.assertNotIn('test-secret', url)

    def test_parallel_names_are_unique_and_confined(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            keys = list(pool.map(lambda _: bed.make_key('../../same agent', 'image.PNG'), range(2000)))
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(k.startswith(bed.PREFIX) and k.count('/') == 1 and k.endswith('.png') for k in keys))

    def test_invalid_expiry_fails_before_client_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'file.txt'
            path.write_text('test')
            for seconds in ['0', '-1', '86401']:
                with patch.object(bed, 'Storage') as client, contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(bed.main(['upload', str(path), '--agent-name', 'test', '--expires-in', seconds]), 1)
                    client.assert_not_called()

    def test_credentials_cannot_be_sent_to_arbitrary_endpoint(self):
        env = {'IMAGE_BED_' + k: v for k, v in {'PROVIDER': 'tos', 'ACCESS_KEY': 'test',
               'SECRET_KEY': 'test', 'BUCKET': 'example-bucket', 'REGION': 'cn-beijing'}.items()}
        for endpoint in ['https://example.com', 'http://tos-cn-beijing.volces.com',
                         'https://tos-cn-beijing.volces.com.evil.example', 'https://cloudcontrol.volces.com']:
            with self.assertRaises(bed.ConfigError):
                bed.config(dict(env, IMAGE_BED_ENDPOINT=endpoint))

    def test_setup_never_overwrites_unrelated_rules(self):
        storage = bed.Storage.__new__(bed.Storage)
        storage.check_version = Mock()
        storage.rules = Mock(return_value=[SimpleNamespace(prefix='other/', status='Enabled', expiration=None)])
        storage.client = Mock()
        with self.assertRaises(bed.ConfigError):
            storage.setup()
        self.assertEqual(storage.client.mock_calls, [])

    def test_filtered_or_wrong_expiration_is_not_cleanup(self):
        rule = SimpleNamespace(prefix=bed.PREFIX, status='Enabled', expiration=SimpleNamespace(days=1))
        self.assertTrue(bed.compatible(rule))
        rule.tags = ['only-tagged-objects']
        self.assertFalse(bed.compatible(rule))
        rule.tags = None
        rule.expiration.days = 7
        self.assertFalse(bed.compatible(rule))

    def test_versioned_bucket_rejected_for_both_providers(self):
        for is_tos in [True, False]:
            for state in ['Enabled', 'Suspended']:
                storage = bed.Storage.__new__(bed.Storage)
                storage.tos, storage.cfg, storage.client = is_tos, {'bucket': 'example-bucket'}, Mock()
                storage.client.get_bucket_version.return_value.status = state
                storage.client.get_bucket_versioning.return_value.status = state
                with self.assertRaises(bed.ConfigError):
                    storage.check_version()

    def test_public_object_is_rejected(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        for status in [200, 206, 302, 404, 500]:
            response.status_code = status
            with patch('requests.get', return_value=response), self.assertRaises(bed.ConfigError):
                bed.ensure_private('https://example.com/image.png?signature=secret')
        response.status_code = 403
        with patch('requests.get', return_value=response) as request:
            bed.ensure_private('https://example.com/image.png?signature=secret')
            self.assertEqual(request.call_args.args[0], 'https://example.com/image.png')

    def test_missing_cleanup_prevents_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'file.txt'
            path.write_text('test')
            with patch.object(bed, 'config', return_value={}), patch.object(bed, 'Storage') as constructor:
                constructor.return_value.check_lifecycle.side_effect = bed.ConfigError('Missing cleanup')
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(bed.main(['upload', str(path), '--agent-name', 'test']), 1)
                constructor.return_value.put.assert_not_called()


if __name__ == '__main__':
    unittest.main()
