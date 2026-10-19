# Gemini and Google Cloud

Relay CX uses Gemini to understand a customer's message and write a grounded reply
from the verified sample company records. The app—not Gemini—decides who can see those
records and whether a support case can be created.

Google ADK is the software library Relay CX uses to connect to Gemini and
record its steps. The website uses Next.js, the backend uses FastAPI, and the
sample records are served by local fake company services.

## What is ready

- Gemini can be used when a key and an available model are configured.
- The project includes files that can help build containers and prepare one
  Google Compute Engine virtual machine.

## What is not ready or not done

- No Google Cloud service has been created or deployed for this project.
- Logging, monitoring, secret access, and company identity still need cloud
  setup.
- Running multiple backend servers safely requires shared storage and safe
  case handling that this demo does not have.
- This is not a Dialogflow CX or Vertex AI deployment.

See the [deployment guide](../deployment/README.md) for the cloud limits and
the [Gemini guide](./GEMINI_INVOCATIONS.md) for what Gemini can and cannot do.


## Mapping to the intended Google customer-experience environment

| Implemented boundary | Google Cloud / Gemini CX mapping | Work still required |
|---|---|---|
| Next.js customer channel | A web channel or Dialogflow CX webhook entry | Build the CX adapter and carry the opaque authenticated session; do not trust channel-supplied account IDs |
| ADK router and specialist | Google ADK agents; possible Agent Engine hosting | Current implementation runs locally. Shared state and transactional action claims are prerequisites for distributed hosting |
| Gemini Developer API client | Gemini model invocation | A Vertex AI client would require ADC/IAM and endpoint changes; an environment project ID alone does not enable it |
| Synthetic identity gateway | Identity Platform/OIDC for customers; IAP for staff | Keep the supplied synthetic identity in the challenge. Federation is a future integration, not an implemented claim |
| SQLite events and JSON-lines log | Cloud Logging REST export from the durable event journal | Optional exporter and Compose overlay are implemented; ADC/IAM, retention and alert policies still require cloud setup |
| Correlated application traces | OpenTelemetry / Cloud Trace | The optional exporter maps request/tool/model events to parented Cloud Trace spans. Transport contracts are tested locally; live cloud delivery is not claimed |
| Single-process Compose runtime | Compute Engine, ext4 persistent disk, Artifact Registry, Cloud Build, Secret Manager and HTTPS proxy | Assets are supplied and locally validated; no cloud resources were created |

The challenge does not provide direct Gemini CX product access. The functioning implementation therefore uses Google ADK and Gemini with the same controlled orchestration, enterprise tools, deterministic permissions and correlated telemetry boundaries. It does not claim to be a deployed Dialogflow CX or Vertex Agent Engine service.
