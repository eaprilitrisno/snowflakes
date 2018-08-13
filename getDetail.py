from helper import *

def add_dbProduct(datas,mydb):
	mycursor = mydb.cursor()
	print("[+] Jumlah Data {} | Input Product".format(len(datas)))
	sql_header = "INSERT INTO `product_data` (`shop_name`,`data-pid`, `data-cid`, `name`, `url`, `image`, `price`) VALUES "
	mysql_rows = []
	for i , row in enumerate(datas):
		shop_name,data_pid,data_cid,name,price,url,image = row
		mysql_rows.append("('{}','{}','{}','{}','{}','{}','{}')".format(shop_name,data_pid,data_cid,name,url,image,price))
	sql_footer = " ON DUPLICATE KEY UPDATE `name`=VALUES(`name`),`data-cid`=VALUES(`data-cid`),`url`=VALUES(`url`),`price`=VALUES(`price`)"
	sql_body=','.join(mysql_rows)
	sql = sql_header+sql_body+sql_footer
	mycursor.execute(sql)
	mydb.commit()
	print("[+] DATA {} record inserted.".format(mycursor.rowcount))

def get_variant(browser):
	variant_data = browser.execute_script('return product_variant')
	resp={}
	for x in variant_data['children']:
		stock = x['stock']
		price = x['price']
		img = x['picture']['original']
		id = x['option_ids'][0]
		resp[id]={'stock':stock,'price':price,'img':img}
	variant_dt = variant_data['variant']
	if len(variant_dt) > 0 :
		for x in variant_dt[0]['option']:
			id = x['id']
			value = x['value']
			resp[id]['value']=value
	return resp

def get_video(html):
	video_tmp = html.find_all(class_='rvm-video-display--item')
	resp = []
	for x in video_tmp:
		resp.append(x.find('iframe').get('src'))
	return '###'.join(resp)

def get_page_detail(browser):
	html = BeautifulSoup(browser.page_source,'html.parser')
	shop_id = html.find(id='shop-id').get('value').strip()
	product_id = html.find(id='product-id').get('value').strip()
	product_name = html.find(id='product-name').get('value').strip()
	product_menu = html.find(id='menu-name').get('value').strip()
	product_price = html.find(id='product_price_int').get('value').strip()
	product_weight = html.find(id='product-weight-kg').get('value').strip()
	product_min_buy = html.find(id='min-order').get('value').strip()
	product_description = html.find(itemprop='description').text.strip().replace('\'','\\\'')
	product_img_str = html.find_all("div", {"class": re.compile("^content-img slick-slide")})
	product_img = '###'.join([img.find('img').get('src') for img in product_img_str])
	variant = str(get_variant(browser)).replace('\'','\\\'')
	video = get_video(html)
	return product_id,product_img,product_name,product_menu,product_min_buy,product_price,product_description,video,variant,product_weight

def add_dbProduct(data,table_detail,mydb):
	mycursor = mydb.cursor()
	sql_header = """INSERT INTO `{}` (
		`data_pid`,
		`image`,
		`name`,
		`etalase`,
		`min_buy`,
		`price`,
		`description`,
		`video`,
		`variant`,
		`weight`) VALUES """.format(table_detail)
	mysql_rows = []
	product_id,product_img,product_name,product_menu,product_min_buy,product_price,product_description,product_video,product_variant,product_weight = data
	mysql_rows.append("('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"%(product_id,product_img,product_name,product_menu,product_min_buy,product_price,product_description,product_video,product_variant,product_weight))
	sql_footer = """ ON DUPLICATE KEY UPDATE
		`data_pid`=VALUES(`data_pid`),
		`image`=VALUES(`image`),
		`name`=VALUES(`name`),
		`etalase`=VALUES(`etalase`),
		`min_buy`=VALUES(`min_buy`),
		`price`=VALUES(`price`),
		`description`=VALUES(`description`),
		`video`=VALUES(`video`),
		`variant`=VALUES(`variant`),
		`weight`=VALUES(`weight`)"""
	sql_body=','.join(mysql_rows)
	sql = sql_header+sql_body+sql_footer
	mycursor.execute(sql)
	mydb.commit()
	print("[+] {} record inserted.".format(mycursor.rowcount))
	#UPDATE STATUS # 0 not uploaded # 1 uploaded # -1 removed
	updated_status='1'
	sql_update = ("UPDATE %s SET `status`='%s' WHERE `data_pid`='%s'"%(table_detail,updated_status,product_id))
	mycursor.execute(sql_update)
	mydb.commit()
	print("[+] Status Updated | Row affected {}.".format(mycursor.rowcount))

def get_product_listDB(table_data,table_detail,mydb):
	mycursor = mydb.cursor()
	date = (datetime.datetime.now().strftime("%Y-%m-%d"))
	sql = "select `date`,`data_pid`,`shop_name`,`url`,`name` from {} where (data_pid) not in (select data_pid from {}) and date ='{}'".format(table_data,table_detail,date)
	mycursor.execute(sql)
	myresult = mycursor.fetchall()
	print('[+] get {} product to get detail'.format(len(myresult)))
	return myresult

def run(root):
	printo('INITIALIZING','center',True)
	mydb=mysql.connector.connect(
		host=ghost,
		user=guser,
		passwd=gpasswd,
		database=gdatabase,
		port=gport)
	print('[+] OK')
	printo('STARTING','center',True)
	datas = get_product_listDB(gtable_data,gtable_detail,mydb)
	if(len(datas) > 0):
		try:
			browser = init_browser(root)
			for row in datas:
				date,data_pid,shop_name,url,name = row
				print('[+] {} - {}'.format(data_pid,name))
				print('[+] {}'.format(url))
				goto_URL(browser,url)
				resp = get_page_detail(browser)
				add_dbProduct(resp,table_detail,mydb)
		except Exception as e:
			print e
		browser.quit()
	else:
		print('[-] No data to get detail | get data list first.')
	printo('FINISH','center',True)

def main():
	root = False
	run(root)

if __name__ == '__main__':
	name()
