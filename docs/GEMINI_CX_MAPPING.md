# Gemini and Google Cloud

Relay CX uses Gemini to help understand a customer's message and select facts
from the sample company records. The app—not Gemini—decides who can see those
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
