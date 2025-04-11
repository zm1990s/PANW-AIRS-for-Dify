## PANW AI Security

**Author:** Matt Zhang

**Version:** 0.0.3

**Type:** tool

**中文文档|Chinese Doc**: [https://github.com/zm1990s/PANW-AIRS-for-Dify/blob/main/README-CN.md](https://github.com/zm1990s/PANW-AIRS-for-Dify/blob/main/README-CN.md)


### Overview

This plugin is a PANW AI Runtime Security API security tool designed for the Dify platform, aiming to enhance the security of AI model and interactions. By integrating Palo Alto Networks' advanced cloud threat detection services, it provides users with comprehensive security protection.

### Prerequisites

Authorized users should refer to the [AI Runtime Security: API Intercept Overview](https://docs.paloaltonetworks.com/ai-runtime-security/activation-and-onboarding/ai-runtime-security-api-intercept-overview) to complete the configuration of AI Runtime Security.

If you have not yet been authorized, please [contact our Palo Alto Networks account manager](https://www.paloaltonetworks.com/about-us/locations).

### Main Features

- **Prompt Detection**: Scans user inputs in Dify applications to prevent prompt injection, large model DoS attacks, and unsafe URLs, ensuring the secure operation of AI models.
- **Model and Data Protection**: Scans the outputs of large models to prevent accidental leakage of sensitive data such as PII; prevents large models from returning malicious URLs or malicious content.
- **Flexible Integration**: Seamlessly integrates into Dify's existing architecture without requiring customized modifications to the model, supporting various integration methods such as workflows and Agents.

### Basic Usage Example

#### Installation and Authorization

Install the plugin via **Marketplace/Github/Local Plugin**, and after installation, click "Authorize" to fill in the authentication information.

![img1](_assets/img1-en.png)

#### Calling in Chatflow

You can call the plugin in Chatflow to retrieve input and output content separately. It is also necessary to use "conditional branches" for judgment. If the detection result includes "allow", the workflow continues; otherwise, static content is returned, the and workflow is stopped.

![img2](_assets/img2-en.png)

The following is an example of calling the input side tool:

![img3](_assets/img3-en.png)

The specific parameters are described as follows:

- **Check Options?** The PANW AIRS Prompt/Response identifier is used to distinguish whether the content to be checked belongs to input or output. Supported values are: `Input Check`,`Output Check`,`Code Input Check` and `Code Output Check`
- **App Name (Optional)**: The name of the Chatflow/Agent, used for logging purposes.
- **User Name (Optional)**: The user identifier for the current application, used for logging purposes.
- **Model Name (Optional)**: The name of the model used by the current application, used for logging purposes.
- **PANW AIRS Profile Name Override (Optional)**: If you want to use a different Profile for this application, you can adjust it through this parameter. The default will use the globally configured Profile Name.

The input judgment component is configured as follows:

![img4](_assets/img4-en.png)

The following is an example of calling the output side tool:

![img5](_assets/img5-en.png)

The output judgment component is configured as follows:

![img6](_assets/img6-en.png)

#### Calling in Agent

![img7](_assets/img7-en.png)

Prompt examples:

> You are a personal information inquiry chatbot.
>
> 
>
> You need to chat with users. Before chatting, you should call the `palo_alto_networks_ai_security_api` tool to check the user's input. If the detection result includes "block", reply to the user with "Input is prohibited", otherwise answer the question normally.
>
> 
>
> If the user is asking about information related to Matt, you need to query the knowledge base for relevant content.
>
> 
>
> Before answering the question, you should call the `palo_alto_networks_ai_security_api` tool to check the output. If the detection result includes "block", reply to the user with "Output is prohibited", otherwise answer the question normally.

### Simple Demo

![img8](_assets/img8-en.png)

## PANW AI Security Tools for Dify

**作者：** Matt Zhang

**版本：** 0.0.3

**类型：** tool

### 概述

该插件是一款适用于 Dify 平台的 PANW AI Runtime Security API 安全工具，旨在增强 AI 模型和数据交互中的安全性，通过集成 Palo Alto Networks 先进的云威胁检测服务，为用户提供全方位的安全防护。

### 前提条件

已获得授权的用户，请参照[此文档](https://docs.paloaltonetworks.com/ai-runtime-security/activation-and-onboarding/ai-runtime-security-api-intercept-overview)完成 AI Runtime Security 的配置。

如还未获得授权，请[联系 Palo Alto Networks 客户经理](https://www.paloaltonetworks.cn/contact)。

### 主要功能

- **提示词检测**：扫描 Dify 应用的用户输入，防止提示词注入、大模型 DoS 攻击、不安全的 URL 等安全问题，确保 AI 模型的安全运行。
- **模型与数据保护**：扫描大模型的输出，防止大模型意外泄露 PII 等敏感数据；防止大模型返回恶意 URL、恶意内容等安全风险。
- **灵活集成**：无缝集成到 Dify 的现有架构中，无需对模型进行定制化修改，支持工作流、Agent 等多种对接方式。

### 基本使用示例

#### 安装及授权

通过 **Marketplace/Github/本地插件**等方式安装插件，安装完毕后点击“去授权”，确保认证成功。

![img1](_assets/img1.png)

#### 在 Chatflow 中调用

可以在 Chatflow 中分别调用插件对输入和输出内容进行检索，同时需要搭配“条件分支”来进行判断，如果检测结果中包含 "allow" 则继续进行工作流，否则返回静态内容，停止工作流。

![img2](_assets/img2.png)

输入侧工具调用示例如下：

<img src="_assets/img3.png" alt="img3" style="zoom:50%;" />

具体参数说明如下：

- 进行输入检查还是输出检查？：PANW AIRS Prompt/Response 标识符，用于区分待检测内容属于输入还是输出
- 应用名称（可选）：该 Chatflow/Agent 的名称，用于日志记录
- 用户名称（可选）：当前应用的用户标识，用于日志记录
- 模型名称（可选）：当前应用所使用的模型名称，用于日志记录
- 指定新的 PANW AIRS Profile Name（可选）：如果想针对该应用使用不同的 Profile，可以通过此参数来调整。默认将会使用全局配置的 Profile Name

输入判断组件配置如下：

<img src="_assets/img4.png" alt="img4" style="zoom:50%;" />

输出侧工具调用示例如下：


<img src="_assets/img5.png" alt="img5" style="zoom:50%;" />


输出判断组件配置如下：


<img src="_assets/img6.png" alt="img6" style="zoom:50%;" />

#### 在 Agent 中调用

<img src="_assets/img7.png" alt="img7" style="zoom:50%;" />

提示词示例：

> 你是一个个人信息查询对话机器人。
>
> 你需要和用户聊天，在聊天前需要先调用 palo_alto_networks_ai_security_api 对用户的输入进行检查，如果检测结果中包含 block，则回复用户“输入已被禁止”，否则请正常回答问题。
>
>  
>
> 如果用户在询问 Matt 相关的信息，需要查询知识库获取相关的内容。
>
>  
>
> 在回答问题前，需要先将你想回答的内容调用 palo_alto_networks_ai_security_api 对输出进行检查，如果检测结果中包含 block，则回复用户“输出已被禁止”，否则请正常回答问题。

### 功能演示

<img src="_assets/img8.png" alt="img8" style="zoom:50%;" />

## Changelog
### v0.0.3
- 新增恶意代码检测功能，与 API 功能对齐

### v0.0.2
- 新增 Profile Name Override 功能，满足不同应用使用不同的安全策略配置需求（注意：全局依然只能共享使用一个 Key）

### v0.0.1
- 初始版本，实现基本的全局凭据配置，输入检查及输出检查
- 支持下列内容的识别：
  - 提示词注入
  - 恶意 URL
  - 敏感数据检测（支持后台此定义策略）
  - SQL 安全
  - Toxic Content