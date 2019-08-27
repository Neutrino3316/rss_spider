FROM python:3.6

COPY . /opt/rss_spider/
WORKDIR /opt/rss_spider

VOLUME ["/opt/rss_spider"]

# install requirements
RUN pip install pip -U
# optional
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install -r requirements.txt

# -u for https://stackoverflow.com/questions/42223834/docker-stucks-when-executing-time-sleep1-in-a-python-loop
ENTRYPOINT ["python", "-u", "run.py"]