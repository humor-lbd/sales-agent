/*
文件作用：
- 在已有 seed 数据基础上追加业务场景覆盖数据。
- 数据只通过 ORD-SC 开头的订单号做幂等 upsert，反复执行不会重复膨胀订单量。
- 订单日期全部基于 CURDATE() 生成，保证“本月、近 30 天、近 6 个月、去年同期”等动态问法始终有数据。

覆盖范围：
- 订单查询：按时间、大区、销售员、订单状态查询。
- 汇总排行：全公司/大区销售额，销售员排行，大区排行，产品排行，最佳/最差商品。
- 趋势对比：环比、同比、近 N 个月月度趋势。
- 图表：折线图、柱状图、饼图，region/rep/category/product 四种维度。
- 异常：大区订单量骤降、产品连续零销售、销售员高退单率、销售员业绩骤降。
- 权限：销售代表、销售经理、销售总监三种角色的数据范围。
*/

SET @today := CURDATE();
SET @month_start := DATE_ADD(MAKEDATE(YEAR(@today), 1), INTERVAL (MONTH(@today) - 1) MONTH);
SET @d_m0 := @today;
SET @d_m1 := GREATEST(DATE_SUB(@today, INTERVAL 1 DAY), @month_start);
SET @d_m2 := GREATEST(DATE_SUB(@today, INTERVAL 2 DAY), @month_start);

SET @region_east := (SELECT id FROM sa_sales_region WHERE name = '华东区' LIMIT 1);
SET @region_south := (SELECT id FROM sa_sales_region WHERE name = '华南区' LIMIT 1);
SET @region_north := (SELECT id FROM sa_sales_region WHERE name = '华北区' LIMIT 1);
SET @region_southwest := (SELECT id FROM sa_sales_region WHERE name = '西南区' LIMIT 1);

SET @rep_zhangwei := (SELECT id FROM sa_sales_rep WHERE name = '张伟' LIMIT 1);
SET @rep_wangfang := (SELECT id FROM sa_sales_rep WHERE name = '王芳' LIMIT 1);
SET @rep_liuyang := (SELECT id FROM sa_sales_rep WHERE name = '刘洋' LIMIT 1);
SET @rep_zhaoxue := (SELECT id FROM sa_sales_rep WHERE name = '赵雪' LIMIT 1);
SET @rep_zhanglei := (SELECT id FROM sa_sales_rep WHERE name = '张磊' LIMIT 1);
SET @rep_zhouli := (SELECT id FROM sa_sales_rep WHERE name = '周丽' LIMIT 1);
SET @rep_zhenghua := (SELECT id FROM sa_sales_rep WHERE name = '郑华' LIMIT 1);
SET @rep_linmin := (SELECT id FROM sa_sales_rep WHERE name = '林敏' LIMIT 1);

SET @sku_phone_huawei := (SELECT id FROM sa_product WHERE sku_code = 'SKU-1001' LIMIT 1);
SET @sku_phone_apple := (SELECT id FROM sa_product WHERE sku_code = 'SKU-1002' LIMIT 1);
SET @sku_laptop := (SELECT id FROM sa_product WHERE sku_code = 'SKU-1003' LIMIT 1);
SET @sku_headphone := (SELECT id FROM sa_product WHERE sku_code = 'SKU-1004' LIMIT 1);
SET @sku_phone_xiaomi := (SELECT id FROM sa_product WHERE sku_code = 'SKU-1005' LIMIT 1);
SET @sku_watch := (SELECT id FROM sa_product WHERE sku_code = 'SKU-8821' LIMIT 1);
SET @sku_vacuum := (SELECT id FROM sa_product WHERE sku_code = 'SKU-2001' LIMIT 1);
SET @sku_dishwasher := (SELECT id FROM sa_product WHERE sku_code = 'SKU-2002' LIMIT 1);
SET @sku_aircon := (SELECT id FROM sa_product WHERE sku_code = 'SKU-2003' LIMIT 1);
SET @sku_shoes := (SELECT id FROM sa_product WHERE sku_code = 'SKU-3001' LIMIT 1);
SET @sku_suit := (SELECT id FROM sa_product WHERE sku_code = 'SKU-3003' LIMIT 1);
SET @sku_bag := (SELECT id FROM sa_product WHERE sku_code = 'SKU-3004' LIMIT 1);
SET @sku_stationery := (SELECT id FROM sa_product WHERE sku_code = 'SKU-4001' LIMIT 1);
SET @sku_books := (SELECT id FROM sa_product WHERE sku_code = 'SKU-4002' LIMIT 1);
SET @sku_giftbox := (SELECT id FROM sa_product WHERE sku_code = 'SKU-4005' LIMIT 1);

INSERT INTO sa_sales_order (
    order_no, rep_id, product_id, region_id, customer_name,
    quantity, unit_price, amount, cost, profit, status, order_date
) VALUES
    -- 本月/近期：保证“本月”“今天/昨天附近”“当前周期”类问题有数据，且覆盖四个大区、多个销售员、四个品类。
    ('ORD-SC-CM-001', @rep_zhangwei, @sku_phone_apple, @region_east, '上海星河数码有限公司', 6, 7999.00, 47994.00, 30600.00, 17394.00, 'COMPLETED', @d_m0),
    ('ORD-SC-CM-002', @rep_zhangwei, @sku_phone_huawei, @region_east, '杭州云栖科技有限公司', 3, 6999.00, 20997.00, 12600.00, 8397.00, 'COMPLETED', @d_m1),
    ('ORD-SC-CM-003', @rep_wangfang, @sku_shoes, @region_east, '南京运动旗舰店', 12, 899.00, 10788.00, 5040.00, 5748.00, 'COMPLETED', @d_m2),
    ('ORD-SC-CM-004', @rep_liuyang, @sku_vacuum, @region_south, '广州万家家居连锁', 5, 4990.00, 24950.00, 14000.00, 10950.00, 'COMPLETED', @d_m0),
    ('ORD-SC-CM-005', @rep_liuyang, @sku_dishwasher, @region_south, '深圳优居广场', 3, 5999.00, 17997.00, 10500.00, 7497.00, 'COMPLETED', @d_m1),
    ('ORD-SC-CM-006', @rep_zhaoxue, @sku_phone_xiaomi, @region_south, '珠海移动渠道中心', 4, 5999.00, 23996.00, 14400.00, 9596.00, 'COMPLETED', @d_m2),
    ('ORD-SC-CM-007', @rep_zhouli, @sku_laptop, @region_north, '北京智采中心', 1, 9999.00, 9999.00, 6800.00, 3199.00, 'COMPLETED', @d_m1),
    ('ORD-SC-CM-008', @rep_zhenghua, @sku_aircon, @region_southwest, '成都蓉城地产', 7, 3299.00, 23093.00, 13300.00, 9793.00, 'COMPLETED', @d_m0),
    ('ORD-SC-CM-009', @rep_linmin, @sku_suit, @region_southwest, '重庆运动集合店', 18, 699.00, 12582.00, 5580.00, 7002.00, 'COMPLETED', @d_m1),
    ('ORD-SC-CM-010', @rep_zhenghua, @sku_bag, @region_southwest, '昆明精品百货', 2, 2599.00, 5198.00, 2200.00, 2998.00, 'COMPLETED', @d_m2),
    ('ORD-SC-CM-011', @rep_zhangwei, @sku_laptop, @region_east, '上海大型集团采购部', 4, 9999.00, 39996.00, 27200.00, 12796.00, 'COMPLETED', @d_m0),
    ('ORD-SC-CM-012', @rep_liuyang, @sku_phone_huawei, @region_south, '广州企业福利平台', 4, 6999.00, 27996.00, 16800.00, 11196.00, 'COMPLETED', @d_m0),
    ('ORD-SC-CM-013', @rep_linmin, @sku_stationery, @region_southwest, '重庆办公用品集采', 30, 99.00, 2970.00, 1200.00, 1770.00, 'COMPLETED', @d_m0),

    -- 默认环比：当工具按“当前区间前一段等长日期”自动推导对比周期时，也能拿到数据。
    ('ORD-SC-MOM-001', @rep_zhangwei, @sku_phone_apple, @region_east, '上海月初对比客户', 2, 7999.00, 15998.00, 10200.00, 5798.00, 'COMPLETED', DATE_SUB(@month_start, INTERVAL 1 DAY)),
    ('ORD-SC-MOM-002', @rep_liuyang, @sku_vacuum, @region_south, '广州月初对比客户', 2, 4990.00, 9980.00, 5600.00, 4380.00, 'COMPLETED', DATE_SUB(@month_start, INTERVAL 2 DAY)),
    ('ORD-SC-MOM-003', @rep_zhenghua, @sku_aircon, @region_southwest, '成都月初对比客户', 3, 3299.00, 9897.00, 5700.00, 4197.00, 'COMPLETED', DATE_SUB(@month_start, INTERVAL 3 DAY)),

    -- 上一周期：保证环比、近 30/60 天对比、历史区间查询都有可比较基线。
    ('ORD-SC-PM-001', @rep_zhangwei, @sku_phone_apple, @region_east, '上海渠道补货中心', 2, 7999.00, 15998.00, 10200.00, 5798.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 32 DAY)),
    ('ORD-SC-PM-002', @rep_wangfang, @sku_giftbox, @region_east, '南京美妆联盟', 4, 899.00, 3596.00, 1400.00, 2196.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 35 DAY)),
    ('ORD-SC-PM-003', @rep_liuyang, @sku_vacuum, @region_south, '广州家电复购客户', 3, 4990.00, 14970.00, 8400.00, 6570.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 34 DAY)),
    ('ORD-SC-PM-004', @rep_zhaoxue, @sku_dishwasher, @region_south, '深圳精装公寓项目', 1, 5999.00, 5999.00, 3500.00, 2499.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 38 DAY)),
    ('ORD-SC-PM-005', @rep_zhanglei, @sku_laptop, @region_north, '北京金融客户采购', 10, 9999.00, 99990.00, 68000.00, 31990.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 50 DAY)),
    ('ORD-SC-PM-006', @rep_zhanglei, @sku_laptop, @region_north, '天津企业办公更新', 8, 9999.00, 79992.00, 54400.00, 25592.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 48 DAY)),
    ('ORD-SC-PM-007', @rep_zhanglei, @sku_headphone, @region_north, '北京影音渠道商', 20, 2299.00, 45980.00, 22000.00, 23980.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 45 DAY)),
    ('ORD-SC-PM-008', @rep_zhouli, @sku_headphone, @region_north, '石家庄门店补货', 3, 2299.00, 6897.00, 3300.00, 3597.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 43 DAY)),
    ('ORD-SC-PM-009', @rep_zhenghua, @sku_aircon, @region_southwest, '成都楼盘二期采购', 4, 3299.00, 13196.00, 7600.00, 5596.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 36 DAY)),
    ('ORD-SC-PM-010', @rep_linmin, @sku_suit, @region_southwest, '重庆运动门店补货', 10, 699.00, 6990.00, 3100.00, 3890.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 33 DAY)),

    -- 月度趋势：跨月铺点，让近 6/12/24 个月趋势与折线图稳定有月份维度。
    ('ORD-SC-TR-001', @rep_zhangwei, @sku_phone_apple, @region_east, '上海趋势样本客户A', 3, 7999.00, 23997.00, 15300.00, 8697.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 6 MONTH), INTERVAL 8 DAY)),
    ('ORD-SC-TR-002', @rep_liuyang, @sku_vacuum, @region_south, '广州趋势样本客户B', 4, 4990.00, 19960.00, 11200.00, 8760.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 5 MONTH), INTERVAL 10 DAY)),
    ('ORD-SC-TR-003', @rep_zhanglei, @sku_laptop, @region_north, '北京趋势样本客户C', 6, 9999.00, 59994.00, 40800.00, 19194.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 4 MONTH), INTERVAL 12 DAY)),
    ('ORD-SC-TR-004', @rep_zhenghua, @sku_aircon, @region_southwest, '成都趋势样本客户D', 8, 3299.00, 26392.00, 15200.00, 11192.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 3 MONTH), INTERVAL 9 DAY)),
    ('ORD-SC-TR-005', @rep_zhangwei, @sku_phone_huawei, @region_east, '杭州趋势样本客户E', 4, 6999.00, 27996.00, 16800.00, 11196.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 2 MONTH), INTERVAL 11 DAY)),
    ('ORD-SC-TR-006', @rep_liuyang, @sku_dishwasher, @region_south, '深圳趋势样本客户F', 3, 5999.00, 17997.00, 10500.00, 7497.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 1 MONTH), INTERVAL 10 DAY)),
    ('ORD-SC-TR-007', @rep_wangfang, @sku_shoes, @region_east, '南京趋势样本客户G', 10, 899.00, 8990.00, 4200.00, 4790.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 1 MONTH), INTERVAL 16 DAY)),

    -- 去年同期：保证同比查询不再出现“去年同期无数据”。
    ('ORD-SC-YOY-001', @rep_zhangwei, @sku_phone_apple, @region_east, '上海去年同期客户', 3, 7999.00, 23997.00, 15300.00, 8697.00, 'COMPLETED', DATE_SUB(@d_m0, INTERVAL 1 YEAR)),
    ('ORD-SC-YOY-002', @rep_liuyang, @sku_vacuum, @region_south, '广州去年同期客户', 3, 4990.00, 14970.00, 8400.00, 6570.00, 'COMPLETED', DATE_SUB(@d_m1, INTERVAL 1 YEAR)),
    ('ORD-SC-YOY-003', @rep_zhenghua, @sku_aircon, @region_southwest, '成都去年同期客户', 5, 3299.00, 16495.00, 9500.00, 6995.00, 'COMPLETED', DATE_SUB(@d_m2, INTERVAL 1 YEAR)),
    ('ORD-SC-YOY-004', @rep_zhouli, @sku_headphone, @region_north, '北京去年同期客户', 4, 2299.00, 9196.00, 4400.00, 4796.00, 'COMPLETED', DATE_SUB(@d_m1, INTERVAL 1 YEAR)),

    -- 异常：华北区过去 4 周订单基线高、近 2 周只保留少量订单，触发“大区订单量骤降”。
    ('ORD-SC-AN-RD-001', @rep_zhouli, @sku_laptop, @region_north, '华北基线客户01', 5, 9999.00, 49995.00, 34000.00, 15995.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 18 DAY)),
    ('ORD-SC-AN-RD-002', @rep_zhouli, @sku_headphone, @region_north, '华北基线客户02', 10, 2299.00, 22990.00, 11000.00, 11990.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 19 DAY)),
    ('ORD-SC-AN-RD-003', @rep_zhouli, @sku_laptop, @region_north, '华北基线客户03', 6, 9999.00, 59994.00, 40800.00, 19194.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 21 DAY)),
    ('ORD-SC-AN-RD-004', @rep_zhouli, @sku_headphone, @region_north, '华北基线客户04', 8, 2299.00, 18392.00, 8800.00, 9592.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 24 DAY)),
    ('ORD-SC-AN-RD-005', @rep_zhouli, @sku_aircon, @region_north, '华北基线客户05', 4, 3299.00, 13196.00, 7600.00, 5596.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 27 DAY)),
    ('ORD-SC-AN-RD-006', @rep_zhanglei, @sku_laptop, @region_north, '张磊历史大单客户01', 7, 9999.00, 69993.00, 47600.00, 22393.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 31 DAY)),
    ('ORD-SC-AN-RD-007', @rep_zhanglei, @sku_headphone, @region_north, '张磊历史大单客户02', 5, 2299.00, 11495.00, 5500.00, 5995.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 37 DAY)),
    ('ORD-SC-AN-RD-008', @rep_zhanglei, @sku_laptop, @region_north, '张磊历史大单客户03', 5, 9999.00, 49995.00, 34000.00, 15995.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 41 DAY)),

    -- 异常：王芳近 30 天有完成、退款、取消订单，退款占比明显偏高，触发“销售员退单率异常”。
    ('ORD-SC-AN-RF-001', @rep_wangfang, @sku_bag, @region_east, '苏州精品店退单01', 2, 2599.00, 5198.00, 2200.00, 2998.00, 'REFUNDED', DATE_SUB(@today, INTERVAL 3 DAY)),
    ('ORD-SC-AN-RF-002', @rep_wangfang, @sku_giftbox, @region_east, '南京美妆退单02', 6, 899.00, 5394.00, 2100.00, 3294.00, 'REFUNDED', DATE_SUB(@today, INTERVAL 4 DAY)),
    ('ORD-SC-AN-RF-003', @rep_wangfang, @sku_shoes, @region_east, '杭州运动退单03', 10, 899.00, 8990.00, 4200.00, 4790.00, 'REFUNDED', DATE_SUB(@today, INTERVAL 5 DAY)),
    ('ORD-SC-AN-RF-004', @rep_wangfang, @sku_shoes, @region_east, '南京运动正常订单', 3, 899.00, 2697.00, 1260.00, 1437.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 6 DAY)),
    ('ORD-SC-AN-RF-005', @rep_wangfang, @sku_giftbox, @region_east, '苏州美妆取消订单', 2, 899.00, 1798.00, 700.00, 1098.00, 'CANCELLED', DATE_SUB(@today, INTERVAL 7 DAY)),

    -- 异常：SKU-4002 只有一笔较早完成订单，之后没有完成销售，触发“产品连续零销售”。
    ('ORD-SC-AN-ZERO-001', @rep_linmin, @sku_books, @region_southwest, '成都图书渠道旧单', 20, 299.00, 5980.00, 2400.00, 3580.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 45 DAY))
ON DUPLICATE KEY UPDATE
    rep_id = VALUES(rep_id),
    product_id = VALUES(product_id),
    region_id = VALUES(region_id),
    customer_name = VALUES(customer_name),
    quantity = VALUES(quantity),
    unit_price = VALUES(unit_price),
    amount = VALUES(amount),
    cost = VALUES(cost),
    profit = VALUES(profit),
    status = VALUES(status),
    order_date = VALUES(order_date);
