from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import requests
import time
import csv
import os
import sys

class GeneralWebscraper:
    def __init__(self, csvFileName):
        self.csvFileName = csvFileName
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument("--test-type")
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.timeout = 15
        self.fieldNames = ['UPC', 'Product Name', 'Category', 'Subcategory', 'In Stock', 'Price', 'Sale', 'Sale Price', 'Unit', 'Image Link', 'Description', 'Product Page Link']
        self.products = []
        self.csvPath = './CsvFiles/'
        self.productImagePath = './ProductImages/'


    def loadCategoryPage(self, url):
        #function loads the category page into the correct place and gets the list of product box elements
        self.driver.get(url)
        time.sleep(5)

        try: 
            #get product boxes
            while self.driver.find_elements_by_xpath("//button[@class='btn-black']"):
                loadMoreBtn = self.driver.find_element_by_xpath("//button[@class='btn-black']")
                self.driver.execute_script("arguments[0].click()", loadMoreBtn)
                time.sleep(2)

            time.sleep(5)
            parentBoxes = self.driver.find_elements_by_xpath("//div[@class='product-list-item_img-holder text-center']")
            return [parentBox.find_element_by_tag_name("a").get_attribute("href") for parentBox in parentBoxes]
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print("Error occured for category at url", url)
            print("Error is ", e, exc_tb.tb_lineno)
            print("Continuing Run")
            return []
            
    def formatUPC(self,upcText):
        if type(upcText)!=str:
            return ""
        lengthOfUPC = 14
        return ('0'*max(0,(lengthOfUPC-len(upcText))))+upcText

    def downloadImage(self, link, parentCat, subCat):
        img_data = requests.get(link).content
        image_link = link.split("medias/")[-1]
        if '.png?' in image_link:
            image_link = image_link.split(".png")[0]+".png"
        elif '.jpg?' in image_link:
            image_link = image_link.split(".jpg")[0]+".jpg"
        else:
            return False
        subFolderName = (parentCat +"_"+ subCat).replace(" ", "_")
        if not os.path.isdir(self.productImagePath+subFolderName):
            os.mkdir(self.productImagePath+subFolderName)
        with open(self.productImagePath+subFolderName+"/"+image_link,'wb') as handler:
            handler.write(img_data)
        return True

    def scrapeProductPage(self,url, category, parentCategory):
        try:
            self.driver.get(url)
            element_present = EC.visibility_of_element_located((By.XPATH, "//img[@class='ng-tns-c405-0']"))
            WebDriverWait(self.driver, self.timeout).until(element_present)
        except TimeoutException:
            print("Time out exception for link", url)
        except Exception as e:
            print("Error occured when getting product page url", url)
            print("Error is ", e)
            print("Continuing Run")
            return {}
        try : 
            productPageLink = url
            title = self.driver.find_element_by_xpath("//img[@class='ng-tns-c405-0']").get_attribute("alt").strip()
            upc = self.formatUPC(self.driver.find_element_by_xpath("//p[@class='product-code ng-star-inserted']").get_attribute("textContent").split(":")[-1].strip())
            imageUrl = self.driver.find_element_by_xpath("//img[@class='ng-tns-c405-0']").get_attribute("src").strip()
            unit = self.driver.find_element_by_xpath("//span[@class='measurement']").get_attribute("textContent")[1:].strip()

            #get product description
            prodDescriptionDropDownElement = self.driver.find_element_by_css_selector("[title*='Product information']")
            prodDescriptionTextElements = prodDescriptionDropDownElement.find_elements_by_xpath("//div[@class='ng-star-inserted']")
            description = " ".join([prodDesc.get_attribute("textContent") for prodDesc in prodDescriptionTextElements if prodDesc.get_attribute("textContent")!=""])
            #clean description
            description = description.replace("\n", " ").strip()


            #determine if out of stock
            inStock = self.driver.find_element_by_xpath("//button[@class='gg-btn primary']").get_attribute("textContent").lower().strip()!="out of stock"

            #get price and sale
            saleElement = self.driver.find_elements_by_xpath("//p[@class='price actual with-discount ng-star-inserted']")
            if saleElement:
                sale = "True"
                originalPrice = self.driver.find_element_by_xpath("//p[@class='price regular ng-star-inserted']").get_attribute("textContent").strip()[1:]  
                salePrice = saleElement[0].find_element_by_xpath("//span[@class='font-weight-bold']").get_attribute("textContent")[1:]+"."+\
                    saleElement[0].find_element_by_xpath("//span[@class='cents font-weight-bold']").get_attribute("textContent")
            else:
                sale = "False"
                salePrice = "0"
                priceElement = self.driver.find_element_by_xpath("//p[@class='price actual ng-star-inserted']")
                originalPrice = priceElement.find_element_by_xpath("//span[@class='font-weight-bold']").get_attribute("textContent")[1:]+"."+\
                    priceElement.find_element_by_xpath("//span[@class='cents font-weight-bold']").get_attribute("textContent")

            downloadImageSuccessful = self.downloadImage(imageUrl, parentCategory, category)
            if not downloadImageSuccessful:
               return {}
            return {
                'UPC':upc,
                'Product Name':title,
                "In Stock": inStock,
                "Price": originalPrice,
                "Sale": sale,
                "Sale Price": salePrice,
                "Unit": unit,
                "Image Link": imageUrl,
                "Description": description,
                "Product Page Link": productPageLink,
                "Category": parentCategory,
                "Subcategory": category
            }
        except Exception as e:
            print("Error occured for processing product page @", url)
            print("Error is ", e)
            print("Continuing Run")
            return {}
        
    def scrapeCategoryPage(self, parentCat, subCat, url):
        productPageLinks = self.loadCategoryPage(url)
        for productPageLink in productPageLinks:
            if type(productPageLink)!=str: continue
            listEle = self.scrapeProductPage(productPageLink, subCat, parentCat)
            if listEle != {} : self.products.append(listEle)
        self.writeCSV(parentCat,subCat)

    def clearProducts(self):
        self.products = []

    def writeCSV(self, parentCat, subCat):
        fileName = (self.csvPath+parentCat+"_"+subCat+".csv").replace(" ", "_")
        with open(fileName, 'w') as csvfile:
            filewriter = csv.DictWriter(csvfile, fieldnames=self.fieldNames, quoting=csv.QUOTE_ALL)
            filewriter.writeheader()
            for productDict in self.products:
                if type(productDict)!= dict:
                    continue
                filewriter.writerow(productDict)
        self.clearProducts()

if __name__ == "__main__":
    csvFileName = "productList.csv"
    webScraper = GeneralWebscraper(csvFileName)
    lines = []
    with open('webscrapePages.txt') as f:
        lines = f.readlines()
    cnt = 0
    skip = float('-inf')
    breakCnt = float('inf')
    for line in lines:
        if cnt < skip: 
            cnt+=1
            continue
        if cnt > breakCnt: break 
        parentCat,subCat,url = line.split("|||")
        print("Processing", url)
        webScraper.scrapeCategoryPage(parentCat,subCat,url)
        cnt+=1
