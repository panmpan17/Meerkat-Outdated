FROM python:3
EXPOSE 80
ENV dbusr=cd4fun_u dbpsw=mlmlml dbhst=10.79.255.103 dbprt=5432 dbname=coding4fun_db path=downloads/
RUN pip3 install markupsafe
RUN pip3 install psycopg2
RUN pip3 install pytz
COPY . .
CMD python3 main.py -dbusr ${dbusr} -dbpsw ${dbpsw} -dbhst ${dbhst} -dbprt ${dbprt} -dbname ${dbname} -path ${path}