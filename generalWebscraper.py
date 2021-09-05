from selenium import webdriver
import math
import time
import csv

import selenium
class GeneralWebscraper:
    def __init__(self, csvFileName):
        #url is url to the product listing page\        
        self.csvFileName = csvFileName

        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument("--test-type")
        self.driver = webdriver.Chrome(executable_path="./chromedriver",options=self.options)

        self.fieldNames = ['SKU', 'UPC', 'Product Name', 'Category', 'Subcategory', 'In Stock', 'Price', 'Sale', 'Sale Price', 'Unit', 'Image Link', 'Description', 'Product Page Link']
        self.products = []

    
    def loadCategoryPage(self, url):
        #for testest
        # return self.driver.find_elements_by_class_name("gtm-product")

        # first find number of times that need to click showMore button 
        #needed since showMore button does not disappear
        self.driver.get(url)
        prodPerRefresh = 24 #seems to be constant
        totalProds = int(self.driver.find_elements_by_xpath("//span[@class='nb-result']")[0].text)
        numPresses = math.ceil((totalProds-prodPerRefresh)/prodPerRefresh)
        if numPresses > 0:
            loadMoreBtn = self.driver.find_element_by_id("showMore")
            
            for _ in range(numPresses):
                self.driver.execute_script("arguments[0].click()", loadMoreBtn)
                time.sleep(0.5)

        return self.driver.find_elements_by_class_name("gtm-product")

    def scrapeProductPage(self, url):
        self.driver.get(url)
        #get UPC
        upc = self.driver.find_elements_by_class_name("about-sku-section")[0].text.split(" ")[-1]
        #get product description
        productDescriptionAttribute = self.driver.find_elements_by_xpath("//div[contains(@class, 'description') and contains(@class, 'light') and contains(@class, 'col-md-10')]")[0]
        productDescriptionAttributeChildren = productDescriptionAttribute.find_elements_by_tag_name("p")
        description = " ".join([att.text for att in productDescriptionAttributeChildren])
        try: 
            #get product image
            productImageElement = self.driver.find_elements_by_xpath("//div[contains(@class, 'medias-slider__media') and contains(@class, 'lazyOwl')]")[0]
            productImageElementUrl = productImageElement.get_attribute("data-zoom-image")
            self.driver.back()
            return [productImageElementUrl,upc,description]
        except:
            return ["no image url", upc, description]
    
    def scrapeProductPageInformation(self,url):
        products = self.loadCategoryPage(url)
        productPageUrls = []
        productImageUrls = []
        for product in products:
            productPageUrls.append(product.find_elements_by_class_name("product-card__thumb")[0].get_attribute("href"))
        for i in range(len(products)):
            productImageUrls.append(self.scrapeProductPage(productPageUrls[i]))
        return productImageUrls

    def scrapeCategoryPage(self, url):
        try: 
            productPageInfo = self.scrapeProductPageInformation(url)
            products = self.loadCategoryPage(url)
            splitUrl = url.split("/")
            category=splitUrl[6].replace("-", " ")
            subCategory=splitUrl[7].replace("-", " ")
            for i,product in enumerate(products):
                productPageUrl,upc,description = productPageInfo[i]
                formId = product.find_element_by_id("addToCartForm")
                sku = product.get_attribute("data-sku")
                inStock = formId.find_elements_by_id("addToCartButton-"+sku) !=[]
                self.products.append({
                    'SKU': sku,
                    'UPC': upc,
                    'Product Name': formId.get_attribute("data-product-name"),
                    'In Stock': str(inStock),
                    'Price': formId.get_attribute("data-product-regular-price"),
                    "Sale": formId.get_attribute("data-product-discount"),
                    'Sale Price': formId.get_attribute("data-product-price"),
                    'Unit': formId.get_attribute("data-unit-size"),
                    'Image Link': productPageUrl, #formId.get_attribute("data-product-image"),
                    'Description': description,
                    'Product Page Link': product.find_elements_by_tag_name("a")[0].get_attribute("href"),
                    'Category': category,
                    'Subcategory': subCategory,
                })
        except Exception as e:
            print("An error occurred when processing this url")
            print("The error is: ", e)
            print("All, some, or none of the products from this category may be copied")
            
    def writeCSV(self):
        with open(self.csvFileName, mode='w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.fieldNames)

            writer.writeheader()
            for productDict in self.products:
                writer.writerow(productDict)

if __name__ == "__main__":
    csvFileName = "productList.csv"
    webScraper = GeneralWebscraper(csvFileName)
    lines = []
    with open('webscrapePages.txt') as f:
        lines = f.readlines()
    cnt = 0
    for url in lines:
        print("Processing", url)
        cnt+=1
        if cnt < 10:
            continue
        webScraper.scrapeCategoryPage(url)

    webScraper.writeCSV()