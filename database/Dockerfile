FROM ubuntu:16.04
ENV DEBIAN_FRONTEND=noninteractive

RUN sudo apt-get update
RUN sudo apt-get -y install git

# Install mysql-5.7 & use the root password ''.
RUN echo "mysql-server mysql-server/root_password password ''" | debconf-set-selections
RUN echo "mysql-server mysql-server/root_password_again password ''" | debconf-set-selections
RUN apt-get -y install mysql-server #-5.7
RUN apt-get -y install libmysqlclient-dev

RUN apt-get -y install python3.6
RUN apt-get -y install python-pip
RUN apt-get -y install python-dev
RUN apt-get -y install python3-dev
RUN pip3 install --upgrade pip

RUN apt-get -y install libcurl4-openssl-dev
RUN apt-get -y install libffi-dev
RUN apt-get -y install libssl-dev
ENV PYCURL_SSL_LIBRARY=openssl

RUN pip3 install flask
RUN pip3 install pymysql
RUN pip3 install numpy
RUN pip3 install pycurl --global-option="--with-openssl"
RUN pip3 install pycrypto
RUN pip3 install python-dateutil

# Packages needed by common ML/DSP systems that depend on the IOT Sensor Framework
RUN pip3 install pandas
RUN pip3 install filterpy
RUN pip3 install httplib2
RUN pip3 install werkzeug
RUN pip3 install hashlib
RUN pip3 install sklearn
RUN pip3 install pykalman
RUN pip3 install scikit-image
RUN pip3 install peakutils
RUN pip3 install hmmlearn
RUN pip3 install git+git://github.com/statsmodels/statsmodels

EXPOSE 3306
EXPOSE 5000
