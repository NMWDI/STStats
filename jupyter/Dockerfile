#
FROM python:3.9

#
WORKDIR .

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#RUN #apt-get update
#RUN apt install libsqlite3-mod-spatialite -y
#
COPY ./requirements.txt .

#
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install --pre jupyterlite

#
COPY . .

RUN jupyter lite init
RUN jupyter lite build --contents content
#CMD ["jupyter", "lite", "serve", "--port", "8008"]