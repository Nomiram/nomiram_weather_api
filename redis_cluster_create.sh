###### redis cluster
# sed -i "s/{yourSecureRedisPassword}/password/g" to change password
source configs.env
mkdir redis-cluster
cd redis-cluster
#create redis.conf
###
cat >redis.conf << EOF
# redis.conf file
port {port}
requirepass $password
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
EOF
###

mkdir -p {7000..7005}
for i in {7000..7005}; do cp redis.conf $i; sed -i "s/{port}/$i/g" $i/redis.conf; done
for i in {7000..7005}; do cd $i; redis-server ./redis.conf --daemonize yes; cd ..; done;
echo yes | redis-cli -a $password --cluster create $clusterIP:7000 $clusterIP:7001 \
$clusterIP:7002 $clusterIP:7003 $clusterIP:7004 $clusterIP:7005 \
--cluster-replicas 1
