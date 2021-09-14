from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains

def processString(s):
    #lower case all characters and only make leading characters upper case
    sArr = s.lower().split(" ")
    sArr = [i.capitalize() for i in sArr if i!=""]
    return " ".join(sArr)


def categoryURLWebscraper(url, textDoc):
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    driver = webdriver.Chrome(executable_path="./chromedriver",options=options)
    driver.get(url)

    # menuDisplayBnt = driver.find_element_by_class_name("dropdown-toggle see-all-menu__btn")
    # driver.execute_script("arguments[0].click()", menuDisplayBnt)
    driver.implicitly_wait(1)
    #need to first clcik menu button to see all menus
    menuSeeAllBtn = driver.find_element_by_xpath("//button[@class='dropdown-toggle see-all-menu__btn']")
    driver.execute_script("arguments[0].click()", menuSeeAllBtn)

    menuElementsParent = driver.find_element_by_xpath("//div[@class='see-all-menu__first-dropdown see-all-menu__dropdown']")
    menuElements = menuElementsParent.find_elements_by_xpath("//div[@class='dropdown-item see-all-menu__dropdown-item']")

    menuElementLinks = []
    for i in range(0,len(menuElements)): 
        menuElement = menuElements[i]
        print("menuElement.text",menuElement.text)
        parentCategoryTitle = processString(menuElement.text.strip())
        hover = ActionChains(driver).move_to_element(menuElement)
        hover.perform()
        #now query for sub categories
        subMenuElementsParents = driver.find_element_by_xpath("//div[@class='see-all-menu__second-dropdown see-all-menu__dropdown']")
        subMenuElements = subMenuElementsParents.find_elements_by_tag_name("a")
        for j in range(1,len(subMenuElements)):

            print(parentCategoryTitle)
            menuElementLinks.append("|||".join([parentCategoryTitle,processString(subMenuElements[j].text),subMenuElements[j].get_attribute('href')]))

    with open (textDoc, 'w') as f:
        for line in menuElementLinks:
            f.write(line)
            f.write('\n')
    
    print(menuElementLinks)
    print("Successfully Written File")

    return

if __name__ == "__main__":
    homeURL = "https://www.longos.com/"
    textDoc = 'webscrapePages.txt'

    categoryURLWebscraper(homeURL, textDoc)