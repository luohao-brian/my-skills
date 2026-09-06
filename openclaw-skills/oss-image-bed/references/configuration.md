# 配置与运行

运行前设置以下环境变量；Bucket 必须已存在。使用标准存储、私有访问且未开启过版本控制的桶。

| 变量 | 值 |
| --- | --- |
| `IMAGE_BED_PROVIDER` | `tos` / `volcengine`，或 `oss` / `aliyun` / `ali` |
| `IMAGE_BED_ACCESS_KEY` | 所选厂商的 AccessKey ID |
| `IMAGE_BED_SECRET_KEY` | 所选厂商的 AccessKey Secret |
| `IMAGE_BED_BUCKET` | 桶名，不含域名或路径 |
| `IMAGE_BED_REGION` | 桶地域，例如 `cn-beijing` |
| `IMAGE_BED_ENDPOINT` | 可选，默认从地域推导官方 HTTPS 外网 endpoint；必须为所选厂商官方对象存储域名 |
| `IMAGE_BED_CUSTOM_DOMAIN` | 可选，已绑定同一桶的 HTTPS 域名；只用于生成访问 URL，不更改 API endpoint |

使用现有火山环境时，在调用进程中映射变量，不把凭证内容复制到文件：

```bash
export IMAGE_BED_PROVIDER=tos
export IMAGE_BED_ACCESS_KEY="$VOLCENGINE_ACCESS_KEY"
export IMAGE_BED_SECRET_KEY="$VOLCENGINE_SECRET_KEY"
export IMAGE_BED_REGION=cn-beijing
export IMAGE_BED_BUCKET=your-private-bucket
```

`VOLCENGINE_ENDPOINT` 可能是控制面域名，不用于 TOS 数据面。运行脚本不自动读取 shell profile、CLI 配置或其他凭证来源。依赖安装可使用 `uv pip install -r {baseDir}/requirements.txt`，再使用该环境的 Python 执行。

## 自动清理

`setup-lifecycle` 是单次部署操作：无任何现有生命周期规则时创建 `image_bed_temp/` 前缀、Enabled、Expiration Days=1 的规则；目标规则已存在时只验证。已有其他规则但缺少兼容规则时停止，交由桶管理员通过官方 API 合并，避免覆盖无关配置或丢失 SDK 不支持的字段。部署期间不能有其他进程更新桶生命周期；此 API 不提供跨进程原子追加。

并发 agent 只运行 `upload`，不运行 setup。上传读取规则，不写桶配置、不使用共享临时文件。规则必须无标签/大小过滤、无转储行为，且精确匹配专用前缀、1 天过期。版本控制必须从未开启，避免删除后保留历史版本。

最小运行权限：上传对象、读取生命周期、读取桶版本状态；部署另需设置生命周期。TOS 使用对应 TOS IAM action，OSS 使用 `oss:PutObject`、`oss:GetBucketLifecycle`、`oss:GetBucketVersioning`，部署另需 `oss:PutBucketLifecycle`。签名凭证还需读取目标对象的权限。

上传使用私有对象 ACL、标准存储、正确的 Content-Type、`Content-Disposition: inline` 和 `Cache-Control: private, no-store`。脚本在上传后检查无签名 URL 不能匿名访问，防止桶策略绕过链接有效期；已下载的副本无法撤回。临时 STS 凭证不在当前配置合同内，使用 AK/SK。

## 输出与失败

成功 JSON：`ok`、`provider`、`bucket`、`object_key`、`url`、`expires_in`（秒）、`expires_at`（UTC）、`size_bytes`、`content_type`、`cleanup`。

`cleanup` 说明 `expiration_days: 1`、`deletion: asynchronous`。不要用它计算精确删除时刻。返回 URL 含临时访问签名，仅向需要使用该文件的调用方交付。

失败 JSON 只包含安全错误类别/代码，配置错误附可操作说明；不输出 SDK 原始异常、HTTP 请求或凭证。网络失败后不要盲目重传大文件；上传后的失败可能已留下待自动清理的对象。

## 官方资料

- [OSS 生命周期 API](https://help.aliyun.com/zh/oss/developer-reference/putbucketlifecycle)
- [OSS 签名 URL](https://help.aliyun.com/zh/oss/developer-reference/sign)
- [OSS 自定义域名与预览](https://help.aliyun.com/zh/oss/user-guide/access-buckets-via-custom-domain-names)
- [TOS 生命周期 API](https://www.volcengine.com/docs/6349/196022)
- [TOS Python SDK](https://github.com/volcengine/ve-tos-python-sdk)
