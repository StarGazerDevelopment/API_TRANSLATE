from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

import httpx


PROVIDER_BRAND_COLORS: dict[str, str] = {
    "openai": "#10a37f",
    "anthropic": "#d4a373",
    "google_gemini": "#8b5cf6",
    "groq": "#f97316",
    "openrouter": "#22c55e",
    "deepseek": "#2563eb",
    "mistral": "#f59e0b",
    "cohere": "#06b6d4",
    "xai": "#ef4444",
    "lm_studio": "#38bdf8",
    "ollama_remote": "#a855f7",
    "localai": "#84cc16",
    "custom_openai": "#64748b",
}

PROVIDER_MODEL_PRESETS: dict[str, list[str]] = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o4-mini"],
    "anthropic": ["claude-3-5-sonnet-latest", "claude-3-7-sonnet-latest", "claude-3-haiku-20240307"],
    "google_gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    "openrouter": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet", "google/gemini-flash-1.5"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "mistral": ["mistral-large-latest", "ministral-8b-latest", "open-mistral-7b"],
    "cohere": ["command-r", "command-r-plus", "command-a"],
    "xai": ["grok-2-latest", "grok-beta"],
    "lm_studio": ["local-model", "mistral-nemo-instruct", "llama-3.1-local"],
    "ollama_remote": ["llama3.1", "mistral", "phi4"],
    "localai": ["gpt-oss", "llama-local", "mixtral-local"],
    "custom_openai": ["custom-model"],
}


def build_logo_text(name: str) -> str:
    words = [part for part in name.replace("-", " ").split() if part]
    if not words:
        return "AI"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def provider(
    slug: str,
    name: str,
    env_var: str,
    transport: str = "openai_compatible",
    base_url: str | None = None,
    category: str = "llm",
) -> dict[str, Any]:
    return {
        "slug": slug,
        "name": name,
        "env_var": env_var,
        "transport": transport,
        "base_url": base_url or "",
        "category": category,
        "logo_text": build_logo_text(name),
        "logo_color": PROVIDER_BRAND_COLORS.get(slug, "#475569"),
        "models": PROVIDER_MODEL_PRESETS.get(slug, []),
    }


PROVIDER_CATALOG: list[dict[str, Any]] = [
    provider("openai", "OpenAI", "OPENAI_API_KEY", base_url="https://api.openai.com/v1"),
    provider("anthropic", "Anthropic Claude", "ANTHROPIC_API_KEY", transport="anthropic", base_url="https://api.anthropic.com/v1/messages"),
    provider("google_gemini", "Google Gemini", "GEMINI_API_KEY", transport="gemini", base_url="https://generativelanguage.googleapis.com/v1beta"),
    provider("groq", "Groq", "GROQ_API_KEY", base_url="https://api.groq.com/openai/v1"),
    provider("openrouter", "OpenRouter", "OPENROUTER_API_KEY", base_url="https://openrouter.ai/api/v1"),
    provider("deepseek", "DeepSeek", "DEEPSEEK_API_KEY", base_url="https://api.deepseek.com/v1"),
    provider("mistral", "Mistral AI", "MISTRAL_API_KEY", base_url="https://api.mistral.ai/v1"),
    provider("cohere", "Cohere", "COHERE_API_KEY", transport="cohere", base_url="https://api.cohere.com/v1/chat"),
    provider("xai", "xAI", "XAI_API_KEY", base_url="https://api.x.ai/v1"),
    provider("ai21", "AI21 Labs", "AI21_API_KEY", base_url="https://api.ai21.com/studio/v1"),
    provider("together", "Together AI", "TOGETHER_API_KEY", base_url="https://api.together.xyz/v1"),
    provider("fireworks", "Fireworks AI", "FIREWORKS_API_KEY", base_url="https://api.fireworks.ai/inference/v1"),
    provider("perplexity", "Perplexity", "PERPLEXITY_API_KEY", base_url="https://api.perplexity.ai"),
    provider("huggingface", "Hugging Face Inference", "HUGGINGFACE_API_KEY", transport="custom"),
    provider("replicate", "Replicate", "REPLICATE_API_KEY", transport="custom"),
    provider("nvidia_nim", "NVIDIA NIM", "NVIDIA_NIM_API_KEY", base_url="https://integrate.api.nvidia.com/v1"),
    provider("sambanova", "SambaNova", "SAMBANOVA_API_KEY", base_url="https://api.sambanova.ai/v1"),
    provider("cerebras", "Cerebras", "CEREBRAS_API_KEY", base_url="https://api.cerebras.ai/v1"),
    provider("moonshot", "Moonshot AI", "MOONSHOT_API_KEY", base_url="https://api.moonshot.cn/v1"),
    provider("zhipu", "Zhipu AI", "ZHIPU_API_KEY", base_url="https://open.bigmodel.cn/api/paas/v4"),
    provider("aws_bedrock", "AWS Bedrock", "AWS_BEDROCK_API_KEY", transport="custom"),
    provider("azure_openai", "Azure OpenAI", "AZURE_OPENAI_API_KEY", transport="azure_openai"),
    provider("vertex_ai", "Google Vertex AI", "VERTEX_AI_API_KEY", transport="custom"),
    provider("ibm_watsonx", "IBM Watsonx", "IBM_WATSONX_API_KEY", transport="custom"),
    provider("oracle_cloud_ai", "Oracle Cloud AI", "ORACLE_CLOUD_AI_API_KEY", transport="custom"),
    provider("alibaba_model_studio", "Alibaba Cloud Model Studio", "ALIBABA_MODEL_STUDIO_API_KEY", transport="custom"),
    provider("tencent_hunyuan", "Tencent Cloud Hunyuan", "TENCENT_HUNYUAN_API_KEY", transport="custom"),
    provider("baidu_qianfan", "Baidu Qianfan", "BAIDU_QIANFAN_API_KEY", transport="custom"),
    provider("sap_ai_core", "SAP AI Core", "SAP_AI_CORE_API_KEY", transport="custom"),
    provider("snowflake_cortex", "Snowflake Cortex", "SNOWFLAKE_CORTEX_API_KEY", transport="custom"),
    provider("anyscale", "Anyscale", "ANYSCALE_API_KEY", base_url="https://api.endpoints.anyscale.com/v1"),
    provider("lepton", "Lepton AI", "LEPTON_API_KEY", transport="custom"),
    provider("baseten", "Baseten", "BASETEN_API_KEY", transport="custom"),
    provider("modal", "Modal", "MODAL_API_KEY", transport="custom"),
    provider("octoai", "OctoAI", "OCTOAI_API_KEY", base_url="https://text.octoai.run/v1"),
    provider("nebius", "Nebius AI Studio", "NEBIUS_API_KEY", base_url="https://api.studio.nebius.ai/v1"),
    provider("novita", "Novita AI", "NOVITA_API_KEY", base_url="https://api.novita.ai/v3/openai"),
    provider("hyperbolic", "Hyperbolic", "HYPERBOLIC_API_KEY", base_url="https://api.hyperbolic.xyz/v1"),
    provider("lambda_ai", "Lambda AI", "LAMBDA_API_KEY", transport="custom"),
    provider("runpod", "RunPod", "RUNPOD_API_KEY", transport="custom"),
    provider("openpipe", "OpenPipe", "OPENPIPE_API_KEY", transport="custom"),
    provider("infermatic", "Infermatic", "INFERMATIC_API_KEY", base_url="https://api.infermatic.ai/v1"),
    provider("featherless", "Featherless", "FEATHERLESS_API_KEY", transport="custom"),
    provider("akash", "Akash Network", "AKASH_API_KEY", transport="custom"),
    provider("deepinfra", "DeepInfra", "DEEPINFRA_API_KEY", base_url="https://api.deepinfra.com/v1/openai"),
    provider("vllm", "VLLM Server", "VLLM_API_KEY", base_url="http://localhost:8001/v1"),
    provider("ollama_remote", "Ollama Remote", "OLLAMA_API_KEY", transport="ollama", base_url="http://localhost:11434/api"),
    provider("localai", "LocalAI", "LOCALAI_API_KEY", base_url="http://localhost:8080/v1"),
    provider("litellm_proxy", "LiteLLM Proxy", "LITELLM_PROXY_API_KEY", base_url="http://localhost:4000/v1"),
    provider("textgen_webui", "Text Generation WebUI", "TEXTGEN_WEBUI_API_KEY", transport="custom"),
    provider("lm_studio", "LM Studio", "LM_STUDIO_API_KEY", base_url="http://localhost:1234/v1"),
    provider("koboldai", "KoboldAI", "KOBOLDAI_API_KEY", transport="custom"),
    provider("open_webui", "Open WebUI", "OPEN_WEBUI_API_KEY", transport="custom"),
    provider("siliconflow", "SiliconFlow", "SILICONFLOW_API_KEY", base_url="https://api.siliconflow.cn/v1"),
    provider("modelscope", "ModelScope", "MODELSCOPE_API_KEY", transport="custom"),
    provider("minimax", "MiniMax", "MINIMAX_API_KEY", transport="custom"),
    provider("ppio", "PPIO", "PPIO_API_KEY", transport="custom"),
    provider("hailuo", "Hailuo AI", "HAILUO_API_KEY", transport="custom"),
    provider("poe", "Poe API", "POE_API_KEY", transport="custom"),
    provider("character_ai", "Character AI", "CHARACTER_AI_API_KEY", transport="custom"),
    provider("you_com", "You.com", "YOU_COM_API_KEY", transport="custom"),
    provider("kimi", "Kimi API", "KIMI_API_KEY", base_url="https://api.moonshot.cn/v1"),
    provider("gmi_cloud", "GMI Cloud", "GMI_CLOUD_API_KEY", transport="custom"),
    provider("vast", "Vast.ai", "VAST_API_KEY", transport="custom"),
    provider("datacrunch", "DataCrunch", "DATACRUNCH_API_KEY", transport="custom"),
    provider("coreweave", "CoreWeave", "COREWEAVE_API_KEY", transport="custom"),
    provider("crusoe", "Crusoe", "CRUSOE_API_KEY", transport="custom"),
    provider("fluidstack", "FluidStack", "FLUIDSTACK_API_KEY", transport="custom"),
    provider("scale_ai", "Scale AI", "SCALE_AI_API_KEY", transport="custom"),
    provider("assemblyai", "AssemblyAI", "ASSEMBLYAI_API_KEY", transport="custom", category="speech"),
    provider("elevenlabs", "ElevenLabs", "ELEVENLABS_API_KEY", transport="custom", category="speech"),
    provider("cartesia", "Cartesia", "CARTESIA_API_KEY", transport="custom", category="speech"),
    provider("deepgram", "Deepgram", "DEEPGRAM_API_KEY", transport="custom", category="speech"),
    provider("gladia", "Gladia", "GLADIA_API_KEY", transport="custom", category="speech"),
    provider("speechmatics", "Speechmatics", "SPEECHMATICS_API_KEY", transport="custom", category="speech"),
    provider("rev_ai", "Rev AI", "REV_AI_API_KEY", transport="custom", category="speech"),
    provider("fal", "Fal AI", "FAL_API_KEY", transport="custom", category="multimodal"),
    provider("stability", "Stability AI", "STABILITY_API_KEY", transport="custom", category="image"),
    provider("black_forest_labs", "Black Forest Labs", "BLACK_FOREST_LABS_API_KEY", transport="custom", category="image"),
    provider("ideogram", "Ideogram", "IDEOGRAM_API_KEY", transport="custom", category="image"),
    provider("leonardo", "Leonardo AI", "LEONARDO_API_KEY", transport="custom", category="image"),
    provider("playground", "Playground AI", "PLAYGROUND_API_KEY", transport="custom", category="image"),
    provider("runway", "Runway", "RUNWAY_API_KEY", transport="custom", category="video"),
    provider("pika", "Pika", "PIKA_API_KEY", transport="custom", category="video"),
    provider("luma", "Luma AI", "LUMA_API_KEY", transport="custom", category="video"),
    provider("tavily", "Tavily", "TAVILY_API_KEY", transport="custom", category="search"),
    provider("serpapi", "SerpAPI", "SERPAPI_API_KEY", transport="custom", category="search"),
    provider("exa", "Exa", "EXA_API_KEY", transport="custom", category="search"),
    provider("brave_search", "Brave Search API", "BRAVE_SEARCH_API_KEY", transport="custom", category="search"),
    provider("wolfram", "Wolfram Alpha API", "WOLFRAM_ALPHA_APP_ID", transport="custom", category="search"),
    provider("rapidapi", "RapidAPI", "RAPIDAPI_KEY", transport="custom"),
    provider("apify", "Apify", "APIFY_API_KEY", transport="custom"),
    provider("supabase_edge", "Supabase Edge Functions", "SUPABASE_EDGE_API_KEY", transport="custom"),
    provider("cloudflare_gateway", "Cloudflare AI Gateway", "CLOUDFLARE_AI_GATEWAY_KEY", transport="custom"),
    provider("workers_ai", "Workers AI", "WORKERS_AI_API_KEY", transport="custom"),
    provider("digitalocean_genai", "DigitalOcean GenAI", "DIGITALOCEAN_GENAI_API_KEY", transport="custom"),
    provider("grok_enterprise", "Grok Enterprise", "GROK_ENTERPRISE_API_KEY", transport="custom"),
    provider("azure_openai_gov", "OpenAI Azure Government", "AZURE_OPENAI_GOV_API_KEY", transport="azure_openai"),
    provider("vertex_partner_models", "Vertex AI Partner Models", "VERTEX_PARTNER_MODELS_API_KEY", transport="custom"),
    provider("custom_openai", "Custom OpenAI-Compatible Provider", "CUSTOM_OPENAI_API_KEY", base_url="https://example.com/v1"),
]


SUPPORTED_ENDPOINTS = {
    "/v1/chat/completions": "chat",
    "/v1/completions": "completion",
    "/v1/embeddings": "embedding",
    "/v1/images": "image",
    "/v1/audio/transcriptions": "audio",
}


def catalog_lookup(slug: str) -> dict[str, str] | None:
    for item in PROVIDER_CATALOG:
        if item["slug"] == slug:
            return item
    return None


@dataclass
class ProviderRuntimeConfig:
    slug: str
    display_name: str
    env_var: str
    api_key: str
    base_url: str
    transport: str
    default_model: str | None
    timeout_seconds: int


class ProviderError(Exception):
    pass


class UnsupportedTransportError(ProviderError):
    pass


class ProviderInvoker:
    async def invoke(self, config: ProviderRuntimeConfig, endpoint_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if config.transport == "openai_compatible":
            return await self._invoke_openai_compatible(config, endpoint_type, payload)
        if config.transport == "anthropic":
            return await self._invoke_anthropic(config, payload)
        if config.transport == "gemini":
            return await self._invoke_gemini(config, payload)
        if config.transport in {"custom", "azure_openai", "cohere", "ollama"}:
            return await self._invoke_openai_compatible(config, endpoint_type, payload)
        raise UnsupportedTransportError(f"Transport '{config.transport}' is not implemented yet.")

    async def _invoke_openai_compatible(
        self,
        config: ProviderRuntimeConfig,
        endpoint_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        route = {
            "chat": "/chat/completions",
            "completion": "/completions",
            "embedding": "/embeddings",
            "image": "/images/generations",
            "audio": "/audio/transcriptions",
        }.get(endpoint_type, "/chat/completions")
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            response = await client.post(
                f"{config.base_url.rstrip('/')}{route}",
                headers={"Authorization": f"Bearer {config.api_key}"},
                json=payload,
            )
        response.raise_for_status()
        return response.json()

    async def _invoke_anthropic(self, config: ProviderRuntimeConfig, payload: Dict[str, Any]) -> Dict[str, Any]:
        model = payload.get("model") or config.default_model or "claude-3-5-sonnet-latest"
        messages = payload.get("messages", [])
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            response = await client.post(
                config.base_url,
                headers={
                    "x-api-key": config.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": payload.get("max_tokens", 1024),
                    "messages": messages,
                },
            )
        response.raise_for_status()
        data = response.json()
        text = "".join(part.get("text", "") for part in data.get("content", []) if isinstance(part, dict))
        return {
            "id": data.get("id", "anthropic-response"),
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "provider_raw": data,
        }

    async def _invoke_gemini(self, config: ProviderRuntimeConfig, payload: Dict[str, Any]) -> Dict[str, Any]:
        model = payload.get("model") or config.default_model or "gemini-1.5-flash"
        messages = payload.get("messages", [])
        prompt_text = "\n".join(item.get("content", "") for item in messages if isinstance(item, dict))
        endpoint = f"{config.base_url.rstrip('/')}/models/{model}:generateContent?key={config.api_key}"
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            response = await client.post(
                endpoint,
                json={"contents": [{"parts": [{"text": prompt_text}]}]},
            )
        response.raise_for_status()
        data = response.json()
        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        return {
            "id": "gemini-response",
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "provider_raw": data,
        }


def catalog_json() -> str:
    return json.dumps(PROVIDER_CATALOG)


def filter_catalog_by_slugs(slugs: Iterable[str]) -> List[dict[str, str]]:
    requested = set(slugs)
    return [item for item in PROVIDER_CATALOG if item["slug"] in requested]
