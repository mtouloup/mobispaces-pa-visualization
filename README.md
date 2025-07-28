
# MobiSpaces Privacy Aware Visualization (PAVA) Backend

  

## Introduction

 The MobiSpaces Privacy Aware Visualization (PAVA) Backend is a Python-based application designed to provide a suite of RESTful API endpoints for data visualization and analysis. This application is built using Flask and serves various endpoints to interact with sensor data, traffic emissions data, and maritime trajectory data.

## Features

-  **User Authentication**: Secure access to API endpoints with token-based authentication.

-  **Data Visualization**: Render and export visual representations of sensor and trajectory data.

-  **Data Export**: Support for exporting data in multiple formats like JSON, CSV, and XLSX.

-  **Swagger UI**: Interactive API documentation and testing interface available at \`/pava\`.

  ## API Endpoints

The application serves the following main endpoints:

1.  **UC2 Endpoints**:

-  `/pava/sensor_data/<sensor_id>`: Get sensor data for a specific sensor.

-  `/pava/traffic`: Get traffic emissions data.

-  `/pava/heat_map`: Get heatmap data for emissions.

- Other endpoints supporting export functionalities.
  
2.  **UC3 Endpoints**:

-  \`/pava/trip_map/<zoom>/<markers>\`: Map visualization for maritime trajectories.

-  \`/pava/data/<number_of_rows>\`: Retrieve a specific number of data rows.

- Aggregated data endpoints for maritime statistics.

- Other endpoints supporting export functionalities.

3.  **Login Endpoint**:

-  `/pava/login`: Endpoint for user authentication.

  Each endpoint may have additional query parameters for specifying data range, format, etc. For detailed usage and parameters, please refer to the Swagger UI at `/pava/`.
  
## Getting Started

### Prerequisites
- Docker Engine
 
### Deployment with Docker

  1.  **Build the Docker Image**:

```shell

docker build -t pava-backend .
```

This command builds a Docker image named \`pava-backend\` using the Dockerfile in the current directory.

2.  **Run the Docker Container**:

```shell

docker run -d -p 80:80 pava-backend

```

This command runs the `pava-backend` image in a detached mode and maps the container's port 80 to the host's port 80.

After running these commands, the PAVA Backend will be up and running on `http://localhost/pava/` or `http://<your-machine-ip>/pava/`.

 ## Contributing

 Contributions to the PAVA Backend are welcome. Please follow the standard git workflow - fork, clone, commit, push, and create pull requests.

## Acknowledgments

This software has been developed thanks to the [MobiSpaces](https://mobispaces.eu) project (Grant agreement ID: 101070279)

## Contact

Marios Touloupou [touloupos@gmail.com]
Evgenia Kapassa [evgeniakapassa@gmail.com]
