## Prisma AIRS AI Gateway

**Author:** zm1990s  
**Version:** 0.0.1  
**Type:** Model Provider

### Description

This plugin connects Dify to the **Palo Alto Networks Prisma AIRS AI Gateway** — a centralized security and observability layer for AI traffic. The gateway sits in front of your LLM providers, enforcing access policies, rate limits, and budget controls while logging all prompts and responses.

The plugin is fully OpenAI-compatible and routes requests through the gateway to any backend LLM you have provisioned in Strata Cloud Manager (SCM).

---

### Prerequisites

- An active **Prisma AIRS** license with flex credits allocated to AI Gateway.
- A cloud account onboarded in **Strata Cloud Manager (SCM)**.
- At least one LLM **Integration** configured in SCM → AI Security → AI Gateway.

---

### Getting Your API Key

1. Log in to [Strata Cloud Manager](https://stratacloudmanager.paloaltonetworks.com).
2. Navigate to **AI Security → AI Gateway**.
3. Click **Create Integration** (or open an existing one).
4. Under **Basic Information**, find or generate the **API Key** for that integration.
5. Note the **slug** — you will need it to construct model names (see below).

---

### Gateway URL

| Deployment | URL |
|------------|-----|
| SaaS (Portkey-hosted, default) | `https://aigw.portkey.ai/v1` |
| Hybrid (self-hosted Data Plane) | Your custom endpoint, e.g. `https://aigw.your-domain.com/v1` |

---

### Plugin Setup in Dify

1. Install the plugin and open its **Settings**.
2. Fill in the provider credentials:

   | Field | Description |
   |-------|-------------|
   | **AI Gateway URL** | Gateway base URL. Use the default for SaaS or enter your hybrid endpoint. |
   | **API Key** | The API key from your SCM integration. |
   | **API Key Header** | HTTP header used to send the key. Default: `x-portkey-api-key`. Change to `Authorization` for standard Bearer auth. |
   | **TLS Certificate Verification** | Disable only when connecting to a gateway with a self-signed certificate. |
   | **Validation Model** | A model available in your integration, used to test the connection (e.g. `@aws-bedrock/amazon.nova-lite-v1:0`). |

3. Click **Save**. The plugin will send a test request to the gateway using the validation model. If the credentials are correct, the provider status turns green.

---

### Adding Models

After the provider is saved, add the models you want to use in Dify:

1. In the provider settings, click **Add Model**.
2. Enter the **Model Name** using the gateway's model identifier format:

   ```
   @<provider-slug>/<model-id>
   ```

   Examples:
   ```
   @aws-bedrock/amazon.nova-lite-v1:0
   @aws-bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
   @openai/gpt-4o
   ```

   The available model IDs depend on the models you provisioned in your SCM integration's **Model Provisioning** step.

3. Optionally override the **AI Gateway URL** or **API Key** for this model if it belongs to a different integration.
4. Click **Save**.

---

### Rate Limits and Budgets

Rate limits and spending budgets are configured per workspace in SCM, not in Dify. The gateway enforces them automatically on every request. Setting a limit to `0` disables the provider for that workspace.

---

### Further Reading

- [Configure AI Gateway – Palo Alto Networks Docs](https://docs.paloaltonetworks.com/ai-runtime-security/administration/configure-ai-gateway)
- [Prisma AIRS Overview](https://docs.paloaltonetworks.com/ai-runtime-security)
