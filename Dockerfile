# use a base python image
FROM python:3.9-slim-bookworm

# set a working directory
WORKDIR /app

# Expose port
ENV PORT 8501

# install required python packages
COPY requirements.txt /app
RUN pip install --upgrade -r requirements.txt

# copy our streamlit code to our image
COPY . /app

# run the streamlit application
CMD ["streamlit","run","EC2_streamlit.py","--server.address","0.0.0.0"]