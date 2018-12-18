FROM tiangolo/uwsgi-nginx:python2.7

COPY ./app app/app/

COPY requirements.txt requirements.txt
COPY SETTINGS.yaml SETTINGS.yaml
RUN pip install -r requirements.txt


EXPOSE 5557
EXPOSE 5558
EXPOSE 8089



CMD /bin/bash
