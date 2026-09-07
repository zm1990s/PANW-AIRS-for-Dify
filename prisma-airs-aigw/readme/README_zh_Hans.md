## Prisma AIRS AI Gateway

**作者：** zm1990s  
**版本：** 0.0.1  
**类型：** 模型提供商

### 描述

本插件将 Dify 接入 **Palo Alto Networks Prisma AIRS AI Gateway** —— 一个集中化的 AI 流量安全与可观测层。网关位于 LLM 提供商前端，在所有请求到达模型之前统一执行访问策略、速率限制和预算控制，并记录所有 Prompt 与响应日志。

插件完全兼容 OpenAI 接口，通过网关将请求路由到您在 Strata Cloud Manager (SCM) 中配置的任意后端模型。

---

### 前置条件

- 有效的 **Prisma AIRS** 许可证，且已在 SCM 中为 AI Gateway 分配 Flex Credits。
- 已在 **Strata Cloud Manager (SCM)** 中完成云账号接入。
- 在 SCM → AI Security → AI Gateway 中已创建至少一个 LLM **集成（Integration）**。

---

### 获取 API Key

1. 登录 [Strata Cloud Manager](https://stratacloudmanager.paloaltonetworks.com)。
2. 导航到 **AI Security → AI Gateway**。
3. 点击 **Create Integration**（或打开已有集成）。
4. 在 **Basic Information** 中找到或生成该集成的 **API Key**。
5. 记录集成的 **slug**，构造模型名称时需要用到（见下文）。

---

### 网关地址

| 部署方式 | 地址 |
|----------|------|
| SaaS（Portkey 托管，默认） | `https://aigw.portkey.ai/v1` |
| Hybrid（自托管 Data Plane） | 您的自定义地址，例如 `https://aigw.your-domain.com/v1` |

---

### 在 Dify 中配置插件

1. 安装插件后，打开其 **设置**。
2. 填写全局凭据：

   | 字段 | 说明 |
   |------|------|
   | **AI Gateway URL** | 网关基础地址。SaaS 使用默认值，Hybrid 填入自定义地址。 |
   | **API Key** | 从 SCM 集成中获取的 API Key。 |
   | **API Key Header** | 发送 API Key 使用的 HTTP 请求头。默认 `x-portkey-api-key`。如需标准 Bearer 认证，改为 `Authorization`。 |
   | **TLS 证书验证** | 仅在连接使用自签名证书的网关时禁用。 |
   | **验证用模型** | 用于测试连通性的模型名称，需在您的集成中已配置（例如 `@aws-bedrock/amazon.nova-lite-v1:0`）。 |

3. 点击 **保存**。插件会用验证用模型向网关发送一次测试请求。凭据正确时，提供商状态变为绿色。

---

### 添加模型

全局凭据保存成功后，添加您想在 Dify 中使用的模型：

1. 在提供商设置中点击 **添加模型**。
2. 按照网关的模型标识格式填写 **模型名称**：

   ```
   @<provider-slug>/<model-id>
   ```

   示例：
   ```
   @aws-bedrock/amazon.nova-lite-v1:0
   @aws-bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
   @openai/gpt-4o
   ```

   可用的模型 ID 取决于您在 SCM 集成的 **Model Provisioning** 步骤中开放的模型范围。

3. 如果该模型属于不同的集成，可选择性地覆盖 **AI Gateway URL** 或 **API Key**。
4. 点击 **保存**。

---

### 速率限制与预算

速率限制和费用预算在 SCM 中按工作空间配置，无需在 Dify 中设置。网关会自动对每个请求执行限制。将限额设置为 `0` 会对该工作空间禁用该提供商。

---

### 参考文档

- [配置 AI Gateway – Palo Alto Networks 官方文档](https://docs.paloaltonetworks.com/ai-runtime-security/administration/configure-ai-gateway)
- [Prisma AIRS 概览](https://docs.paloaltonetworks.com/ai-runtime-security)
