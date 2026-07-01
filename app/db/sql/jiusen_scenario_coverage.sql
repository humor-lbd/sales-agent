/*
文件作用：
- 基于山西玖森百立科技服务有限公司“咪婴伴侣”业务，追加一套母婴 O2O/商城/直播/服务场景数据。
- 只写入 JS 开头的销售员、SKU-JS 开头的产品、ORD-JS 开头的订单，重复执行不会重复膨胀。
- 日期使用 CURDATE() 动态生成，覆盖本月、环比、同比、近 6 个月趋势和异常检测。

业务映射：
- 华北区：山西太原主阵地，偏同城母婴服务、产后修复、陪诊。
- 华东区：华东合作城市与母婴商城，偏商城、课程和直播转化。
- 华南区：华南直播电商和服务试点，偏直播带货、母婴用品。
- 西南区：西南服务试点，故意构造近期订单下滑，用于异常检测。
*/

SET @today := CURDATE();
SET @month_start := DATE_ADD(MAKEDATE(YEAR(@today), 1), INTERVAL (MONTH(@today) - 1) MONTH);
SET @d0 := @today;
SET @d1 := GREATEST(DATE_SUB(@today, INTERVAL 1 DAY), @month_start);
SET @d2 := GREATEST(DATE_SUB(@today, INTERVAL 2 DAY), @month_start);
SET @d3 := GREATEST(DATE_SUB(@today, INTERVAL 3 DAY), @month_start);

INSERT INTO sa_sales_region (id, name) VALUES
    (1, '华东区'),
    (2, '华南区'),
    (3, '华北区'),
    (4, '西南区')
ON DUPLICATE KEY UPDATE
    name = VALUES(name);

SET @region_east := (SELECT id FROM sa_sales_region WHERE name = '华东区' LIMIT 1);
SET @region_south := (SELECT id FROM sa_sales_region WHERE name = '华南区' LIMIT 1);
SET @region_north := (SELECT id FROM sa_sales_region WHERE name = '华北区' LIMIT 1);
SET @region_southwest := (SELECT id FROM sa_sales_region WHERE name = '西南区' LIMIT 1);

INSERT INTO sa_sales_rep (id, name, region_id, role, email) VALUES
    (9101, '于博同', @region_north, 'SALES_DIRECTOR', 'yubotong@jiusenbaili.com'),
    (9102, '太原母婴服务经理', @region_north, 'SALES_MANAGER', 'taiyuan.manager@jiusenbaili.com'),
    (9103, '李娜-太原产康顾问', @region_north, 'SALES_REP', 'lina.ck@jiusenbaili.com'),
    (9104, '王璐-太原母婴顾问', @region_north, 'SALES_REP', 'wanglu.my@jiusenbaili.com'),
    (9105, '周敏-陪诊顾问', @region_north, 'SALES_REP', 'zhoumin.pz@jiusenbaili.com'),
    (9106, '张蕾-华北BD顾问', @region_north, 'SALES_REP', 'zhanglei.bd@jiusenbaili.com'),
    (9107, '华东母婴商城经理', @region_east, 'SALES_MANAGER', 'east.manager@jiusenbaili.com'),
    (9108, '陈悦-华东商城顾问', @region_east, 'SALES_REP', 'chenyue.mall@jiusenbaili.com'),
    (9109, '林岚-华东直播运营', @region_east, 'SALES_REP', 'linlan.live@jiusenbaili.com'),
    (9110, '华南直播电商经理', @region_south, 'SALES_MANAGER', 'south.manager@jiusenbaili.com'),
    (9111, '刘珊-华南电商顾问', @region_south, 'SALES_REP', 'liushan.ec@jiusenbaili.com'),
    (9112, '何洁-华南直播顾问', @region_south, 'SALES_REP', 'hejie.live@jiusenbaili.com'),
    (9113, '西南母婴服务经理', @region_southwest, 'SALES_MANAGER', 'southwest.manager@jiusenbaili.com'),
    (9114, '郑怡-西南服务顾问', @region_southwest, 'SALES_REP', 'zhengyi.service@jiusenbaili.com'),
    (9115, '唐敏-西南咨询顾问', @region_southwest, 'SALES_REP', 'tangmin.consult@jiusenbaili.com')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    region_id = VALUES(region_id),
    role = VALUES(role),
    email = VALUES(email);

INSERT INTO sa_product (id, sku_code, name, category, unit_price, cost, status) VALUES
    (9201, 'SKU-JS-1001', '咪婴伴侣月嫂到家服务包', '同城母婴服务', 6999.00, 4200.00, 'ACTIVE'),
    (9202, 'SKU-JS-1002', '产后修复基础疗程', '产后修复服务', 3999.00, 1800.00, 'ACTIVE'),
    (9203, 'SKU-JS-1003', '盆底肌修复专业疗程', '产后修复服务', 2999.00, 1200.00, 'ACTIVE'),
    (9204, 'SKU-JS-1004', '新生儿护理上门服务', '同城母婴服务', 1299.00, 620.00, 'ACTIVE'),
    (9205, 'SKU-JS-1005', '育儿嫂短期照护服务', '同城母婴服务', 4999.00, 3100.00, 'ACTIVE'),
    (9206, 'SKU-JS-2001', '孕产营养礼包', '母婴用品', 699.00, 350.00, 'ACTIVE'),
    (9207, 'SKU-JS-2002', '婴儿洗护安心套装', '母婴用品', 199.00, 80.00, 'ACTIVE'),
    (9208, 'SKU-JS-2003', '纸尿裤月度组合', '母婴用品', 399.00, 210.00, 'ACTIVE'),
    (9209, 'SKU-JS-2004', '宝宝辅食营养包', '母婴用品', 299.00, 150.00, 'ACTIVE'),
    (9210, 'SKU-JS-3001', '孕期健康咨询会员', '健康咨询服务', 599.00, 120.00, 'ACTIVE'),
    (9211, 'SKU-JS-3002', '陪诊服务单次卡', '陪诊服务', 299.00, 90.00, 'ACTIVE'),
    (9212, 'SKU-JS-3003', '产检陪诊安心包', '陪诊服务', 1299.00, 420.00, 'ACTIVE'),
    (9213, 'SKU-JS-4001', '育儿科普课程年卡', '育儿课程', 399.00, 80.00, 'ACTIVE'),
    (9214, 'SKU-JS-4002', '早教启蒙直播课', '育儿课程', 999.00, 260.00, 'ACTIVE'),
    (9215, 'SKU-JS-5001', '电商直播母婴爆品礼包', '直播电商', 1599.00, 760.00, 'ACTIVE'),
    (9216, 'SKU-JS-5002', '家庭收纳保洁套餐', '家庭生活服务', 899.00, 410.00, 'ACTIVE'),
    (9217, 'SKU-JS-9001', '老版纸质孕育课程包', '育儿课程', 199.00, 70.00, 'ACTIVE')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    category = VALUES(category),
    unit_price = VALUES(unit_price),
    cost = VALUES(cost),
    status = VALUES(status);

SET @p_yuesao := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-1001' LIMIT 1);
SET @p_ck_base := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-1002' LIMIT 1);
SET @p_ck_pendi := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-1003' LIMIT 1);
SET @p_babycare := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-1004' LIMIT 1);
SET @p_nanny := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-1005' LIMIT 1);
SET @p_nutrition := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-2001' LIMIT 1);
SET @p_wash := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-2002' LIMIT 1);
SET @p_diaper := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-2003' LIMIT 1);
SET @p_food := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-2004' LIMIT 1);
SET @p_health := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-3001' LIMIT 1);
SET @p_clinic := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-3002' LIMIT 1);
SET @p_clinic_pack := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-3003' LIMIT 1);
SET @p_course := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-4001' LIMIT 1);
SET @p_live_course := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-4002' LIMIT 1);
SET @p_live_bundle := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-5001' LIMIT 1);
SET @p_cleaning := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-5002' LIMIT 1);
SET @p_old_course := (SELECT id FROM sa_product WHERE sku_code = 'SKU-JS-9001' LIMIT 1);

INSERT INTO sa_sales_order (
    order_no, rep_id, product_id, region_id, customer_name,
    quantity, unit_price, amount, cost, profit, status, order_date
) VALUES
    -- 本月经营看板：覆盖销售汇总、大区排名、销售员排名、产品排名、品类图表。
    ('ORD-JS-CM-001', 9103, @p_yuesao, @region_north, '太原小店区宝妈社群A', 2, 6999.00, 13998.00, 8400.00, 5598.00, 'COMPLETED', @d0),
    ('ORD-JS-CM-002', 9104, @p_ck_base, @region_north, '太原晋源产康中心客户', 4, 3999.00, 15996.00, 7200.00, 8796.00, 'COMPLETED', @d1),
    ('ORD-JS-CM-003', 9105, @p_clinic, @region_north, '山西白求恩医院陪诊客户', 8, 299.00, 2392.00, 720.00, 1672.00, 'COMPLETED', @d2),
    ('ORD-JS-CM-004', 9103, @p_ck_pendi, @region_north, '太原五峰国际产康客户', 3, 2999.00, 8997.00, 3600.00, 5397.00, 'COMPLETED', @d0),
    ('ORD-JS-CM-005', 9104, @p_nanny, @region_north, '太原高新区双职工家庭', 1, 4999.00, 4999.00, 3100.00, 1899.00, 'COMPLETED', @d2),
    ('ORD-JS-CM-006', 9108, @p_live_bundle, @region_east, '杭州母婴商城团购客户', 12, 1599.00, 19188.00, 9120.00, 10068.00, 'COMPLETED', @d0),
    ('ORD-JS-CM-007', 9109, @p_diaper, @region_east, '上海直播间纸尿裤团购', 50, 399.00, 19950.00, 10500.00, 9450.00, 'COMPLETED', @d1),
    ('ORD-JS-CM-008', 9108, @p_course, @region_east, '南京孕育科普会员群', 20, 399.00, 7980.00, 1600.00, 6380.00, 'COMPLETED', @d3),
    ('ORD-JS-CM-009', 9111, @p_nutrition, @region_south, '广州宝妈福利社群', 20, 699.00, 13980.00, 7000.00, 6980.00, 'COMPLETED', @d0),
    ('ORD-JS-CM-010', 9112, @p_live_course, @region_south, '深圳早教直播课转化客户', 10, 999.00, 9990.00, 2600.00, 7390.00, 'COMPLETED', @d1),
    ('ORD-JS-CM-011', 9111, @p_wash, @region_south, '广州母婴洗护社群', 40, 199.00, 7960.00, 3200.00, 4760.00, 'COMPLETED', @d2),
    ('ORD-JS-CM-012', 9114, @p_babycare, @region_southwest, '成都新手妈妈上门护理客户', 3, 1299.00, 3897.00, 1860.00, 2037.00, 'COMPLETED', @d2),
    ('ORD-JS-CM-013', 9115, @p_health, @region_southwest, '重庆孕期健康咨询客户', 5, 599.00, 2995.00, 600.00, 2395.00, 'COMPLETED', @d3),
    ('ORD-JS-CM-014', 9103, @p_yuesao, @region_north, '太原月嫂服务企业团购', 8, 6999.00, 55992.00, 33600.00, 22392.00, 'COMPLETED', @d0),
    ('ORD-JS-CM-015', 9104, @p_ck_base, @region_north, '太原产后修复中心团购', 10, 3999.00, 39990.00, 18000.00, 21990.00, 'COMPLETED', @d1),
    ('ORD-JS-CM-016', 9109, @p_live_bundle, @region_east, '华东直播母婴爆品专场', 60, 1599.00, 95940.00, 45600.00, 50340.00, 'COMPLETED', @d0),
    ('ORD-JS-CM-017', 9111, @p_nutrition, @region_south, '华南孕产营养礼包团购', 80, 699.00, 55920.00, 28000.00, 27920.00, 'COMPLETED', @d1),

    -- 默认环比对比周期：本月 1 日之前的等长窗口有数据。
    ('ORD-JS-MOM-001', 9103, @p_ck_base, @region_north, '太原产康月末预约客户', 2, 3999.00, 7998.00, 3600.00, 4398.00, 'COMPLETED', DATE_SUB(@month_start, INTERVAL 1 DAY)),
    ('ORD-JS-MOM-002', 9108, @p_live_bundle, @region_east, '华东直播月末复购客户', 5, 1599.00, 7995.00, 3800.00, 4195.00, 'COMPLETED', DATE_SUB(@month_start, INTERVAL 2 DAY)),
    ('ORD-JS-MOM-003', 9111, @p_nutrition, @region_south, '华南母婴用品月末客户', 8, 699.00, 5592.00, 2800.00, 2792.00, 'COMPLETED', DATE_SUB(@month_start, INTERVAL 3 DAY)),
    ('ORD-JS-MOM-004', 9114, @p_babycare, @region_southwest, '西南上门护理月末客户', 2, 1299.00, 2598.00, 1240.00, 1358.00, 'COMPLETED', DATE_SUB(@month_start, INTERVAL 4 DAY)),

    -- 去年同期：覆盖同比分析。
    ('ORD-JS-YOY-001', 9103, @p_yuesao, @region_north, '太原去年同期月嫂客户', 1, 6999.00, 6999.00, 4200.00, 2799.00, 'COMPLETED', DATE_SUB(@d0, INTERVAL 1 YEAR)),
    ('ORD-JS-YOY-002', 9108, @p_live_bundle, @region_east, '华东去年同期商城客户', 4, 1599.00, 6396.00, 3040.00, 3356.00, 'COMPLETED', DATE_SUB(@d1, INTERVAL 1 YEAR)),
    ('ORD-JS-YOY-003', 9111, @p_nutrition, @region_south, '华南去年同期礼包客户', 10, 699.00, 6990.00, 3500.00, 3490.00, 'COMPLETED', DATE_SUB(@d2, INTERVAL 1 YEAR)),
    ('ORD-JS-YOY-004', 9114, @p_babycare, @region_southwest, '西南去年同期护理客户', 2, 1299.00, 2598.00, 1240.00, 1358.00, 'COMPLETED', DATE_SUB(@d3, INTERVAL 1 YEAR)),

    -- 月度趋势：近 6 个月都有母婴业务数据，支撑趋势文本和折线图。
    ('ORD-JS-TR-001', 9103, @p_yuesao, @region_north, '太原趋势样本客户01', 2, 6999.00, 13998.00, 8400.00, 5598.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 6 MONTH), INTERVAL 7 DAY)),
    ('ORD-JS-TR-002', 9108, @p_live_bundle, @region_east, '华东趋势样本客户02', 6, 1599.00, 9594.00, 4560.00, 5034.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 5 MONTH), INTERVAL 9 DAY)),
    ('ORD-JS-TR-003', 9111, @p_diaper, @region_south, '华南趋势样本客户03', 30, 399.00, 11970.00, 6300.00, 5670.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 4 MONTH), INTERVAL 10 DAY)),
    ('ORD-JS-TR-004', 9104, @p_ck_base, @region_north, '太原趋势样本客户04', 3, 3999.00, 11997.00, 5400.00, 6597.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 3 MONTH), INTERVAL 8 DAY)),
    ('ORD-JS-TR-005', 9109, @p_course, @region_east, '华东趋势样本客户05', 18, 399.00, 7182.00, 1440.00, 5742.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 2 MONTH), INTERVAL 12 DAY)),
    ('ORD-JS-TR-006', 9112, @p_live_course, @region_south, '华南趋势样本客户06', 8, 999.00, 7992.00, 2080.00, 5912.00, 'COMPLETED', DATE_ADD(DATE_SUB(@month_start, INTERVAL 1 MONTH), INTERVAL 11 DAY)),

    -- 西南区过去 4 周基线高、近 2 周只有少量订单，触发大区订单量骤降。
    ('ORD-JS-RD-001', 9114, @p_babycare, @region_southwest, '成都西南基线客户01', 1, 1299.00, 1299.00, 620.00, 679.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 16 DAY)),
    ('ORD-JS-RD-002', 9115, @p_health, @region_southwest, '重庆西南基线客户02', 1, 599.00, 599.00, 120.00, 479.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 18 DAY)),
    ('ORD-JS-RD-003', 9114, @p_cleaning, @region_southwest, '成都西南基线客户03', 1, 899.00, 899.00, 410.00, 489.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 20 DAY)),
    ('ORD-JS-RD-004', 9115, @p_clinic_pack, @region_southwest, '重庆西南基线客户04', 1, 1299.00, 1299.00, 420.00, 879.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 22 DAY)),
    ('ORD-JS-RD-005', 9114, @p_babycare, @region_southwest, '成都西南基线客户05', 1, 1299.00, 1299.00, 620.00, 679.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 24 DAY)),
    ('ORD-JS-RD-006', 9115, @p_health, @region_southwest, '重庆西南基线客户06', 1, 599.00, 599.00, 120.00, 479.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 26 DAY)),
    ('ORD-JS-RD-007', 9114, @p_cleaning, @region_southwest, '成都西南基线客户07', 1, 899.00, 899.00, 410.00, 489.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 28 DAY)),
    ('ORD-JS-RD-008', 9115, @p_clinic_pack, @region_southwest, '重庆西南基线客户08', 1, 1299.00, 1299.00, 420.00, 879.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 30 DAY)),
    ('ORD-JS-RD-009', 9114, @p_babycare, @region_southwest, '成都西南基线客户09', 1, 1299.00, 1299.00, 620.00, 679.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 32 DAY)),
    ('ORD-JS-RD-010', 9115, @p_health, @region_southwest, '重庆西南基线客户10', 1, 599.00, 599.00, 120.00, 479.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 34 DAY)),
    ('ORD-JS-RD-011', 9114, @p_cleaning, @region_southwest, '成都西南基线客户11', 1, 899.00, 899.00, 410.00, 489.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 36 DAY)),
    ('ORD-JS-RD-012', 9115, @p_clinic_pack, @region_southwest, '重庆西南基线客户12', 1, 1299.00, 1299.00, 420.00, 879.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 38 DAY)),

    -- 张蕾前 30 天高业绩、近 30 天无完成单，触发销售员业绩骤降。
    ('ORD-JS-PD-001', 9106, @p_yuesao, @region_north, '太原渠道BD历史大单01', 5, 6999.00, 34995.00, 21000.00, 13995.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 35 DAY)),
    ('ORD-JS-PD-002', 9106, @p_nanny, @region_north, '太原渠道BD历史大单02', 4, 4999.00, 19996.00, 12400.00, 7596.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 42 DAY)),
    ('ORD-JS-PD-003', 9106, @p_ck_base, @region_north, '太原渠道BD历史大单03', 6, 3999.00, 23994.00, 10800.00, 13194.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 50 DAY)),

    -- 周敏近 30 天退款偏高，触发销售员退单率异常，并覆盖 REFUNDED/CANCELLED 状态。
    ('ORD-JS-RF-001', 9105, @p_clinic, @region_north, '太原陪诊退单客户01', 4, 299.00, 1196.00, 360.00, 836.00, 'REFUNDED', DATE_SUB(@today, INTERVAL 3 DAY)),
    ('ORD-JS-RF-002', 9105, @p_clinic_pack, @region_north, '太原产检陪诊退单客户02', 1, 1299.00, 1299.00, 420.00, 879.00, 'REFUNDED', DATE_SUB(@today, INTERVAL 4 DAY)),
    ('ORD-JS-RF-003', 9105, @p_health, @region_north, '太原健康咨询退单客户03', 2, 599.00, 1198.00, 240.00, 958.00, 'REFUNDED', DATE_SUB(@today, INTERVAL 5 DAY)),
    ('ORD-JS-RF-004', 9105, @p_clinic, @region_north, '太原陪诊取消客户04', 1, 299.00, 299.00, 90.00, 209.00, 'CANCELLED', DATE_SUB(@today, INTERVAL 6 DAY)),

    -- 老版课程包最后一次销售较早，之后不再出单，触发产品连续零销售。
    ('ORD-JS-ZERO-001', 9109, @p_old_course, @region_east, '华东老版课程清仓客户', 20, 199.00, 3980.00, 1400.00, 2580.00, 'COMPLETED', DATE_SUB(@today, INTERVAL 55 DAY))
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
