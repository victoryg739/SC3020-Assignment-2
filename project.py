
from interface import startWindow
'''
Try these complex query examples:
SELECT s_acctbal, s_name, n_name, p_partkey, p_mfgr, s_address, s_phone, s_comment FROM part, supplier, partsupp, nation, region WHERE p_partkey = ps_partkey and s_suppkey = ps_suppkey and p_size = 23 and p_type like '%STEEL' and s_nationkey = n_nationkey and n_regionkey = r_regionkey and r_name = 'EUROPE' and ps_supplycost = (select min(ps_supplycost) from partsupp, supplier, nation, region where p_partkey = ps_partkey and s_suppkey = ps_suppkey and s_nationkey = n_nationkey and n_regionkey = r_regionkey and r_name = 'EUROPE') ORDER BY s_acctbal DESC, n_name, s_name, p_partkey LIMIT 10
SELECT ps_partkey, SUM(ps_supplycost * ps_availqty) AS value FROM partsupp JOIN supplier ON ps_suppkey = s_suppkey JOIN nation ON s_nationkey = n_nationkey WHERE n_name = 'GERMANY' GROUP BY ps_partkey HAVING SUM(ps_supplycost * ps_availqty) > (SELECT SUM(ps_supplycost * ps_availqty) * 0.0001000000e-2 FROM partsupp JOIN supplier ON ps_suppkey = s_suppkey JOIN nation ON s_nationkey = n_nationkey WHERE n_name = 'GERMANY') LIMIT 10;
SELECT l_returnflag, l_linestatus, SUM(l_quantity) AS sum_qty, SUM(l_extendedprice) AS sum_base_price, SUM(l_extendedprice * (1-l_discount)) AS sum_disc_price, SUM(l_extendedprice * (1-l_discount) * (1+l_tax)) AS sum_charge, AVG(l_quantity) AS avg_qty, AVG(l_extendedprice) AS avg_price, AVG(l_discount) AS avg_disc, COUNT(*) AS count_order FROM lineitem WHERE l_shipdate <= '1998-12-01'::date - interval '90 days' GROUP BY l_returnflag, l_linestatus ORDER BY l_returnflag, l_linestatus LIMIT 100;
SELECT * FROM part WHERE p_size BETWEEN 10 AND 15 EXCEPT SELECT * FROM part WHERE p_size = 13 LIMIT 100;
SELECT 100.00 * SUM(CASE WHEN p_type LIKE 'PROMO%' THEN l_extendedprice * (1 - l_discount) ELSE 0 END) / SUM(l_extendedprice * (1 - l_discount)) AS promo_revenue FROM lineitem JOIN part ON l_partkey = p_partkey WHERE l_shipdate >= '1995-09-01'::date AND l_shipdate < ('1995-09-01'::date + INTERVAL '1 month') LIMIT 100;
'''
startWindow()
