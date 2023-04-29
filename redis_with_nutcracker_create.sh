
########## redis with nutcracker(twemproxy)
source configs.env
mkdir redis-twemproxy
cd redis-twemproxy
#create redis.conf
###
cat >redis.conf << EOF
# redis.conf file
port {port}
requirepass $password
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
EOF
###

mkdir -p {7000..7003};
for i in {7000..7003}; do cp redis.conf $i; sed -i "s/{port}/$i/g" $i/redis.conf; done

for i in {7002..7003}; do echo slaveof $clusterIP $(echo $i-2|bc) >> $i/redis.conf; done
for i in {7002..7003}; do echo masterauth {yourSecureRedisPassword} >> $i/redis.conf; done
for i in {7000..7003}; do cd $i; redis-server ./redis.conf --daemonize yes; cd ..; done;

###
cat >nutcracker.conf << EOF
#nutcracker config file
redis:
 listen: 0.0.0.0:22121
 hash: fnv1a_64
 distribution: ketama
 redis: true
 server_retry_timeout: 100
 server_failure_limit: 500
 redis_auth: {yourSecureRedisPassword}
 servers:
 - $clusterIP:7000:1 db-redis-1
 - $clusterIP:7001:1 db-redis-2
 timeout: 400
EOF
###
nutcracker -c nutcracker.yml -v 11