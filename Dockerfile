FROM ultralytics/yolov5:latest
WORKDIR /usr/src/calgary_traffic/yolov5
COPY . /usr/src/calgary_traffic
EXPOSE 5002
RUN pip3 install --upgrade -r ../requirements.txt
RUN apt-get update && apt-get install supervisor -y
ENTRYPOINT sh -c "supervisord -c ../supervisord.conf & streamlit run ../app/app.py --server.port=5002 --server.address=0.0.0.0"