import os
import csv
    
fieldNames = ['UPC', 'Product Name', 'Category', 'Subcategory', 'In Stock', 'Price', 'Sale', 'Sale Price', 'Unit', 'Image Link', 'Description', 'Product Page Link']



def csvFileCombine(csvFilePath):
    directory = os.fsencode(csvFilePath)
    productArr = []
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".csv"):
            with open(csvFilePath+filename,'r') as data:
                rows = csv.reader(data)
                header = []
                for i,r in enumerate(rows):
                    if i == 0: 
                        header = r
                        continue
                    ele = {}
                    for j,c in enumerate(r):
                        ele[header[j]] = c
                    productArr.append(ele)

    print("productArr", productArr)
    
    #now write to file
    with open(csvFilePath+"allProducts.csv", 'w') as csvfile:
        filewriter = csv.DictWriter(csvfile, fieldnames=fieldNames)
        filewriter.writeheader()
        for productDict in productArr:
            if type(productDict) != dict:
                continue
            filewriter.writerow(productDict)
                    


if __name__=='__main__':
    csvFilePath = 'CsvFiles/'
    csvFileCombine(csvFilePath)