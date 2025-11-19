# PowerShell script to generate gRPC Python stubs using a Docker container
# Requires Docker installed.
# Workaround for local Python 3.13 build issues with grpcio-tools.

param(
    [string]$ProtoDir = "proto",
    [string]$OutDir = "."
)

if (-not (Test-Path $ProtoDir)) {
    Write-Error "Proto directory '$ProtoDir' not found"; exit 1
}

# Using namely/protoc-all image which bundles protoc + plugins.
# It will output generated code in $OutDir. Adjust language tag.

docker run --rm -v ${PWD}:/workspace -w /workspace namely/protoc-all:1.56_2 \`n  -f weather.proto -l python -o $OutDir -d $ProtoDir

Write-Host "Generation complete. Check weather_pb2.py and weather_pb2_grpc.py in $OutDir"