#!/bin/sh
mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "GRANT ALL ON \`test\_%\`.* TO '$MYSQL_USER'@'%'; FLUSH PRIVILEGES;"
