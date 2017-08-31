drop table if exists clients;
create table clients (
    id integer primary key autoincrement,
    hostname TEXT,
    display_name TEXT,
    static_vpn_ip TEXT,
    lan_subnet TEXT,
    lan_subnet_len INTEGER,
    status INTEGER,
    date_added DATE
);
