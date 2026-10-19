# vlab

**vlab** is a laboratory integration project that provides two main components:

1. **Communication Agent** — bridges the gap between a hospital system, such as a LIS or LIMS, and laboratory devices. It exposes a Web API to manage devices, test orders, and results, abstracting the details of the supported communication protocols.
2. **Laboratory Device Simulator** — simulates a device via a command-line interface, allowing you to test communication, order queries, and result transmission.

**Version:** `0.0.1` — initial release.

> This documentation describes the interface and behaviors defined for version `0.0.1`. Some implementation details, such as error codes and authentication, are not specified here.

## Table of Contents

- [Requirements and Environment](#requirements-and-environment)
- [General Architecture](#general-architecture)
- [Accessing the Agent on a Hospital Network](#accessing-the-agent-on-a-hospital-network)
- [Communication Agent](#communication-agent)
    - [Conventions](#conventions)
    - [1. Connect a Device](#1-connect-a-device)
    - [2. List Devices](#2-list-devices)
    - [3. Get Device Details](#3-get-device-details)
    - [4. Configure a Device](#4-configure-a-device)
    - [5. Delete a Device Configuration](#5-delete-a-device-configuration)
    - [6. List Serial Ports](#6-list-serial-ports)
    - [7. Query Results](#7-query-results)
    - [8. Query Results by Sample](#8-query-results-by-sample)
    - [9. List Test Orders](#9-list-test-orders)
    - [10. Send Test Orders to a Device](#10-send-test-orders-to-a-device)
- [Hospital System Integration Contract](#hospital-system-integration-contract)
- [Data Models](#data-models)
- [Device Simulator](#device-simulator)
    - [Available Commands](#available-commands)
    - [Simulator Configuration](#simulator-configuration)
    - [Simulated Tests](#simulated-tests)
- [Integration Flow](#integration-flow)
- [Version Notes and Limitations](#version-notes-and-limitations)

---

## Requirements and Environment

The project uses **Poetry** for dependency and Python environment management.

In the project root, activate the virtual environment with:

```bash
eval $(poetry env activate)
```

Run all project commands within this environment.

### Starting the Components

After activating the Poetry environment, the components can be started from the project root.

**Laboratory Device Simulator**

```bash
python -m vlab.laboratory_apparatus
```

**Communication Agent**

```bash
uvicorn vlab.agent.app:app
```

By default, Uvicorn typically uses `127.0.0.1:8000`. To allow connections from other devices on the local network, the agent must listen on a network-accessible interface, for example using `--host 0.0.0.0`, and the selected port must be allowed in the firewall. The actual address and port depend on how the agent is launched and the network configuration.

---

## General Architecture

```text
Hospital System (LIS / LIMS)
          |
          | Agent Web API
          v
vlab Agent
          |
          | Serial or TCP/IP
          v
Laboratory Device
```

The agent centralizes communication with devices and integration with the hospital system. Protocol details, messages, and specificities of each device are handled by the agent and the specific device configuration.

The simulator allows exercising this flow without necessarily relying on a physical laboratory device.

---

## Accessing the Agent on a Hospital Network

In many installations, the `vlab` agent runs on a computer within the hospital's local network, close to the laboratory devices. The hospital system, on the other hand, may be hosted on a cloud server. In this scenario, the cloud server normally cannot initiate a direct connection to a private IP address on the hospital network.

One integration option is to have the hospital application load a page in the browser of a computer that has local network access. The JavaScript on that page can then send HTTP requests directly to the agent's local address.

```text
Cloud-hosted Hospital System
              |
              | Loads web application
              v
Browser on a hospital network computer
              |
              | JavaScript / HTTP to local IP
              v
vlab Agent on the local network
              |
              | Serial or TCP/IP
              v
Laboratory Device
```

For example, if the agent is accessible at `http://192.168.1.50:8000`, the browser can make requests to that address, provided the computer is on the correct network and the network rules permit the connection.

**Key Considerations for This Architecture:**

- **Network Access:** The computer running the browser needs to reach the agent's IP and port. The address `127.0.0.1` refers to the computer running the browser itself, not the agent server, unless both are on the same machine.
- **CORS:** If the web application and the agent have different origins, the agent must explicitly allow the web application's origin via CORS configuration. Indiscriminately allowing any origin is not recommended.
- **HTTPS and Mixed Content:** If the hospital page is served over HTTPS, the browser may block requests to the agent over HTTP. The access strategy must take browser security policies into account, for example by serving the agent over HTTPS or adopting an appropriate network architecture.
- **Authorization and Exposure:** The agent should not be exposed to the Internet without adequate security controls. Restricting local network access, validating origins, and implementing authentication/authorization when necessary are important measures. CORS alone is not an authentication mechanism.
- **Browser Policies:** Access to private network addresses may be subject to additional restrictions depending on the browser and its configuration. The integration should be tested in the real hospital environment.

This approach allows the browser to act as a communication bridge between the cloud-hosted application and the local agent, without requiring the cloud server to route traffic directly to the hospital's private network.

---

## Communication Agent

The examples below use `/api/v1` as the endpoint prefix. Paths should be adjusted if the application is mounted with a different prefix.

### Conventions

- Request and response body examples use JSON.
- `String`, `Integer`, `Boolean`, and `Date` indicate the expected field types.
- Fields marked as optional may be omitted or set to null, depending on the implementation.
- For serial port paths in route parameters, replace each `/` with `_`. For example, `/dev/ttyUSB0` becomes `_dev_ttyUSB0`.
- In TCP connections, the device address is usually its IP address. In serial connections, the address corresponds to the port identifier/path used by the agent.

---

### 1. Connect a Device

`POST /api/v1/connect_device`

Initiates a connection to a device via a serial port or TCP/IP.

**Body — TCP/IP**

```json
{
  "address": "192.168.1.50",
  "port": 5001
}
```

- `address` (`String`): IP address of the device.
- `port` (`Integer`): TCP port opened by the device when the device acts as a server and the agent connects as a client.

**Body — Serial Port**

```json
{
  "address": "/dev/ttyUSB0",
  "baudrate": 9600,
  "bytesize": 8,
  "parity": "N",
  "stopbits": 1
}
```

For a serial connection, `port` is not required. `address` identifies the serial port.

Serial parameters are optional. If not provided in the request or the configuration file, default values are used:

| Parameter | Default Value |
| :--- | :--- |
| `baudrate` | `9600` |
| `bytesize` | `8` |
| `parity` | `"N"` |
| `stopbits` | `1` |

**Indicated Response**

```json
{
  "detail": "Proccess add"
}
```

The response indicated by the project confirms that the request was added to the connection process. The HTTP status code for this response is not specified in this documentation.

---

### 2. List Devices

`GET /api/v1/devices`

Returns a list of connected or known devices.

**Response Example**

```json
[
  {
    "address": "/dev/ttyUSB0",
    "name": "Analisador laboratorial",
    "protocol": "HL7",
    "has_contract": true
  }
]
```

Fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `address` | `String` | Device address. In TCP, usually the IP; in serial, a unique identifier generated by the agent. |
| `name` | `String` (optional) | Name of the device. |
| `protocol` | `String` (optional) | Configured communication protocol, e.g., `HL7` or `ASTM`. |
| `has_contract` | `Boolean` | Indicates whether a specific contract is configured for the device. |

A specific contract allows describing device specificities, including test identifier mappings.

---

### 3. Get Device Details

`GET /api/v1/device/{address}`

Returns data for the device identified by the address.

**Example**

```http
GET /api/v1/device/_dev_ttyUSB0
```

When the serial address contains `/`, replace it with `_` in the URL path.

---

### 4. Configure a Device

`POST /api/v1/config_device`

Configures the communication protocol and, optionally, a specific contract for a device. The protocol must be provided even when the device uses the agent's default contract.

**Body**

```json
{
  "device_address": "/dev/ttyUSB0",
  "protocol": "HL7",
  "contract": {
    "message_codes": {
      "QBP_Q21": "query_exam_orders",
      "ORU_R01": "result_exam_orders"
    },
    "exame_system": {
      "00001": "00001"
    },
    "table_coding": {
      "00001": "LOCAL"
    }
  }
}
```

Body fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `device_address` | `String` | Address of the device to configure. |
| `protocol` | `String` | Communication protocol used by the device, e.g., `HL7` or `ASTM`. |
| `contract` | `Object` (optional) | Device-specific rules. If omitted, the agent uses the default contract. |

Contract fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `message_codes` | `Object` | Maps message codes used by the device to the agent's logical operations. |
| `exame_system` | `Object` | Maps test IDs from the hospital system (keys) to device-recognized IDs (values). |
| `table_coding` | `Object` | Maps device test IDs to their respective coding table. |

Logical operations referenced in `message_codes` include:

- `query_exam_orders`: query test orders for a sample.
- `result_exam_orders`: send test results.

In the example, `QBP_Q21` is associated with querying orders and `ORU_R01` with sending results. Actual codes depend on the protocol and device.

**Success Response — HTTP 201**

```json
{
  "detail": "Config saved"
}
```

---

### 5. Delete a Device Configuration

`DELETE /api/v1/delete_contact/{address}`

Removes the contract/configuration associated with the device address, following the behavior described for this operation.

**Example**

```http
DELETE /api/v1/delete_contact/_dev_ttyUSB0
```

For serial addresses, replace `/` with `_` in the URL path.

> **Warning:** The endpoint name provided in the specification is `delete_contact`, although the description refers to deleting a contract. Verify the name in the published codebase before changing or documenting it as `delete_contract`.

---

### 6. List Serial Ports

`GET /api/v1/serial_ports`

Lists available serial ports for connecting devices.

**Response Example**

```json
[
  {
    "id": "/dev/ttyUSB0",
    "name": "USB Serial Device",
    "description": "USB Serial Port",
    "display": "USB Serial Device:USB Serial Port:/dev/ttyUSB0"
  }
]
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `String` | Identifier/path of the serial port. |
| `name` | `String` (optional) | Device name. |
| `description` | `String` (optional) | Device description. |
| `display` | `String` | Display string composed of name, description, and port identifier. |

Values for `name` and `description` depend on information provided by the operating system and device.

---

### 7. Query Results

`GET /api/v1/exam_results`

Returns test results saved by the agent. In addition to this endpoint, the agent automatically sends results to the hospital system when received from a device.

**Response Example**

```json
[
  {
    "sample_id": "1234",
    "exam_id": "00001",
    "exam_description": "Hemograma Completo",
    "table_coding": "LOCAL",
    "observations": [
      {
        "type_value": "NM",
        "observation_code": "718-7",
        "observation_description": "Hemoglobina",
        "system_coding": "LN",
        "value": "14.2",
        "unity": "g/dL",
        "reference_range": "12.0-16.0",
        "abnormal": "N",
        "property": "C",
        "status": "F"
      }
    ]
  }
]
```

Result fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | `String` | Sample identifier. |
| `exam_id` | `String` | Test identifier. |
| `exam_description` | `String` | Test description. |
| `table_coding` | `String` | Coding table used to identify the test. |
| `observations` | `Array` | List of observations/results comprising the test. |

Each object in `observations` contains:

| Field | Description |
| :--- | :--- |
| `type_value` | Data type of the result (e.g., `NM` indicates a numeric value). |
| `observation_code` | Code for the observation or measured parameter. |
| `observation_description` | Human-readable description of the observation. |
| `system_coding` | Coding system to which the observation code belongs. |
| `value` | Result value. |
| `unity` | Unit of measurement, where applicable. |
| `reference_range` | Reference range, where applicable. |
| `abnormal` | Abnormality indicator provided for the result. |
| `property` | Observation property code, according to the protocol used. |
| `status` | Result status, according to the protocol used. |

Field values such as `type_value`, `property`, `abnormal`, and `status` depend on the protocol and the message received. The example is illustrative and not an exhaustive list of accepted values.

---

### 8. Query Results by Sample

`GET /api/v1/exam_results/{sample_id}`

Returns the result associated with the specified sample identifier.

**Example**

```http
GET /api/v1/exam_results/1234
```

The response structure matches that of `GET /api/v1/exam_results`, filtered for the specified sample.

---

### 9. List Test Orders

`GET /api/v1/exam_orders`

Returns test orders that were sent to the agent and, consequently, to the devices.

**Response Example**

```json
[
  {
    "id": "1234",
    "order_control": "NW",
    "patient": {
      "id": 1,
      "name": "Ana",
      "last_name": "Manuel",
      "birth": "20010423",
      "gender": "F"
    },
    "exams": [
      {
        "sample_id": "1234",
        "exam_id": "00001",
        "exame_description": "Hemograma Completo",
        "exam_result_status": "O"
      }
    ]
  }
]
```

The structure of the `patient` and `exams` objects is described in [Data Models](#data-models).

---

### 10. Send Test Orders to a Device

`POST /api/v1/exam_orders/{address}`

Sends a list of test orders to the specified device.

**Body**

```json
{
  "app_id": "LIS01",
  "facility_id": "HOSPITAL01",
  "exam_orders": [
    {
      "id": "1234",
      "order_control": "NW",
      "patient": {
        "id": 1,
        "name": "Ana",
        "last_name": "Manuel",
        "birth": "20010423",
        "gender": "F"
      },
      "exams": [
        {
          "sample_id": "1234",
          "exam_id": "00001",
          "exame_description": "Hemograma Completo",
          "exam_result_status": "O"
        }
      ]
    }
  ]
}
```

Top-level fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `app_id` | `String` | Hospital system identifier. |
| `facility_id` | `String` | Healthcare facility identifier. |
| `exam_orders` | `Array` | Test orders to send. |

The URL `address` parameter identifies the target device. For serial port paths, replace `/` with `_`.

---

## Hospital System Integration Contract

To receive orders and send results, the hospital system must expose the following endpoints. The agent uses the URL configured for the hospital system.

### Query Test Orders by Sample

`GET /exam_orders/{sample_id}`

When a device needs to process a sample but does not have a locally registered order, the agent can query this endpoint on the hospital system.

**Expected Response**

```json
{
  "patient": {
    "id": 1,
    "name": "Ana",
    "last_name": "Manuel",
    "birth": "20010423",
    "gender": "F"
  },
  "exam_orders": [
    {
      "sample_id": "1234",
      "exam_id": "00001",
      "exame_description": "Hemograma Completo",
      "exam_result_status": "O"
    }
  ]
}
```

The response contains patient details and the list of tests requested for the sample.

---

### Receive Results Sent by the Agent

`POST /send_exam_results`

After receiving results from a device, the agent forwards them to this endpoint in the hospital system.

The request body follows the same structure as items returned by `GET /api/v1/exam_results`.

**Body Example**

```json
{
  "sample_id": "1234",
  "exam_id": "00001",
  "exam_description": "Hemograma Completo",
  "table_coding": "LOCAL",
  "observations": [
    {
      "type_value": "NM",
      "observation_code": "718-7",
      "observation_description": "Hemoglobina",
      "system_coding": "LN",
      "value": "14.2",
      "unity": "g/dL",
      "reference_range": "12.0-16.0",
      "abnormal": "N",
      "property": "C",
      "status": "F"
    }
  ]
}
```

The hospital system should parse and persist the result according to its internal data models.

---

## Data Models

### `Patient`

Represents the patient associated with a test order.

```json
{
  "id": 1,
  "name": "Ana",
  "last_name": "Manuel",
  "birth": "20010423",
  "gender": "F"
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `Integer` | Patient identifier. |
| `name` | `String` | Patient first name. |
| `last_name` | `String` | Patient last name. |
| `birth` | `Date` | Date of birth in `YYYYMMDD` format. |
| `gender` | `String` | Gender indicated by `M` or `F`. |

---

### `Exam`

Represents a test included in an order.

```json
{
  "sample_id": "1234",
  "exam_id": "00001",
  "exame_description": "Hemograma Completo",
  "exam_result_status": "O"
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `sample_id` | `String` | Sample identifier. |
| `exam_id` | `String` | Test identifier. |
| `exame_description` | `String` | Test description. |
| `exam_result_status` | `String` | Result/order status according to the system and protocol code. |

---

### Test Order

An order combines an identifier, an order control code, a patient, and a list of tests.

```json
{
  "id": "1234",
  "order_control": "NW",
  "patient": {
    "id": 1,
    "name": "Ana",
    "last_name": "Manuel",
    "birth": "20010423",
    "gender": "F"
  },
  "exams": [
    {
      "sample_id": "1234",
      "exam_id": "00001",
      "exame_description": "Hemograma Completo",
      "exam_result_status": "O"
    }
  ]
}
```

- `id` (`String`): Order identifier; in the described implementation, it may match the sample identifier.
- `order_control` (`String`): Order control code.
- `patient` (`Patient`): Patient data.
- `exams` (`Array<Exam>`): Tests included in the order.

---

## Device Simulator

The simulator is a command-line application. Once launched, it waits for user input commands to manage rack samples, query orders, and simulate an analysis.

### Available Commands

| Command | Parameter | Description |
| :--- | :--- | :--- |
| `q` | — | Terminates the simulator. |
| `clear` | — | Clears the screen/terminal. |
| `set_sample` | `sample_id` and observation data | Places a sample in the rack and defines the analysis results. |
| `remove_sample` | `sample_id` | Removes a sample from the rack. |
| `show_sample` | `sample_id` | Checks/displays if a sample is in the rack. |
| `clear_rack` | — | Removes all samples from the rack. |
| `show_exam_orders` | — | Displays the list of test orders. |
| `analyze` | — | Executes the simulated analysis and sends the result. |

---

### Defining a Sample

Use `set_sample` followed by the sample identifier and observation data.

**Example**

```text
set_sample 1234 code = 718-7; value = 14.2; unity = g/dL, type_value = NM; ref_min = 12.0; ref_max = 16.0
```

The observation definition process can be repeated to add more parameters to the same sample, following the format supported by the simulator.

Fields used in the example:

- `code`: Observation code; the example uses `718-7`, a LOINC code.
- `value`: Simulated measured value.
- `unity`: Result unit.
- `type_value`: Value type; e.g., `NM` for a numeric value.
- `ref_min` and `ref_max`: Lower and upper bounds of the reference range.

After placing the sample in the rack, run `analyze` to simulate the run and send the results.

---

### Simulator Configuration

Configuration Example:

```ini
# Transport and protocol
SERIAL_MODE = true
PROTOCOL = "HL7"
MODE = "P"

# Serial connection
APPARATUS_SERIAL_PORT = "/tmp/agent"
BAUDRATE = 9600
BYTESIZE = 8
PARITY = "N"
STOPBITS = 1

# TCP/IP connection
AGENT_TCP_PORT = 5000
APPARATUS_TCP_PORT = 5001
TCP_HOST = "127.0.0.1"
GATEWAY_MAX_CLIENT = Infinit
APPARATUS_AS_SERVER = false

# Hospital system
URL_LIS_SERVER = "http://localhost:8000"
```

| Parameter | Description |
| :--- | :--- |
| `SERIAL_MODE` | Specifies whether communication uses serial (`true`) or TCP/IP (`false`). |
| `PROTOCOL` | Communication protocol used by the simulator. |
| `MODE` | Simulator operating mode. The example uses `P`, associated with production mode. |
| `APPARATUS_SERIAL_PORT` | Serial port used by the simulated device. |
| `BAUDRATE` | Serial communication baud rate. |
| `BYTESIZE` | Number of data bits in serial communication. |
| `PARITY` | Serial parity configuration. |
| `STOPBITS` | Number of stop bits in serial communication. |
| `AGENT_TCP_PORT` | Agent TCP port, when applicable to the simulator setup. |
| `APPARATUS_TCP_PORT` | TCP port associated with the simulated device. |
| `TCP_HOST` | IP address the simulator connects to when acting as a TCP client. |
| `GATEWAY_MAX_CLIENT` | Limit of accepted clients when the agent acts as a TCP server, per supported config. |
| `APPARATUS_AS_SERVER` | Indicates whether the simulated device acts as a server in TCP mode. |
| `URL_LIS_SERVER` | Base URL of the integrated hospital system. |

**Configuration Note:** The value `Infinit` was preserved as provided in the specification. Verify in the source code whether this literal is accepted by the implementation or should be replaced by an integer or another value.

---

### Simulated Tests

The simulator supports the following tests:

| ID | Test |
| :--- | :--- |
| `00001` | Complete Blood Count (CBC) |
| `00020` | COVID-19 Test (RT-PCR) |
| `00030` | HIV Rapid Test / Serology (HIV 1/2) |
| `00040` | Malaria Test (Thick Smear & Direct Examination) |

---

## Integration Flow

A typical integration workflow consists of:

1. Start the agent and configure hospital system access.
2. Query available serial ports if using serial communication.
3. Connect the device via `POST /api/v1/connect_device`.
4. Configure the protocol and, if necessary, the specific contract via `POST /api/v1/config_device`.
5. Send test orders to the device, or let the agent query the hospital system when an order is not locally available.
6. The device processes the sample and sends the results to the agent.
7. The agent saves the results and automatically forwards them to `POST /send_exam_results` in the hospital system.
8. Query saved results from the agent via `GET /api/v1/exam_results` or `GET /api/v1/exam_results/{sample_id}`.

Exact behavior depends on each device's protocol and configuration.
