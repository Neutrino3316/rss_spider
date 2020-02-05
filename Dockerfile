FROM python

COPY . /opt/rss_spider/
WORKDIR /opt/rss_spider

VOLUME ["/opt/rss_spider"]

# update pip
RUN pip install pip -U
# use tsinghua pip mirror in mainland China
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
# install requirements
RUN pip install -r requirements.txt

# -u for https://stackoverflow.com/questions/42223834/docker-stucks-when-executing-time-sleep1-in-a-python-loop
ENTRYPOINT ["python", "-u", "run.py"]