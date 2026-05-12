FROM ubuntu:latest
LABEL authors="vbaho"

RUN pip install uv

# Copy only the files needed for installation to improve cache
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv pip install --system --requirement pyproject.toml


ENTRYPOINT ["top", "-b"]
