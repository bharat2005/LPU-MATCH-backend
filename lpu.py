from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
)
import time

service = Service("C:\\Users\\bhara\\abc\\Uni-Match-backend\\c\\chromedriver.exe")

def verify_user_deep(registration_number, ums_password):
   
    try:
        driver = webdriver.Chrome(service=service)
        driver.get("https://ums.lpu.in/lpuums/LoginNew.aspx")


        for attempt in range(3):
            try:
                reg_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "txtU"))
                )
                reg_field.clear()
                reg_field.send_keys(registration_number)
                break
            except StaleElementReferenceException:
                time.sleep(1)


        for attempt in range(3):
            try:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "TxtpwdAutoId_8767"))
                )
                password_field.clear()
                password_field.send_keys(ums_password)
                break
            except StaleElementReferenceException:
                time.sleep(1)

    
        for attempt in range(3):
            try:
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "iBtnLogins150203125"))
                )
                login_button.click()
                break
            except StaleElementReferenceException:
                time.sleep(1)


        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        if "Important Links and Information" in driver.page_source:
            try:
                profile_img = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "p_picture"))
                )
                profile_img_url = profile_img.get_attribute("src")


            except NoSuchElementException:
                profile_img_url = None

    
            try:
                profile_name = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "p_name"))
                )

                profile_name_text = driver.execute_script("return arguments[0].innerText;", profile_name)

            except NoSuchElementException:
                profile_name_text = None

            return {
                "status": "Login Successful",
                "profile_name": profile_name_text,
                "profile_img_url": profile_img_url,
            }
        else:
            return {"status": "Invalid Details"}

    except StaleElementReferenceException:
        return {"status": "Stale element reference error"}
    except NoSuchElementException:
        return {"status": "Element not found"}
    except TimeoutException:
        return {"status": "Timeout error"}
    except Exception as e:
        return {"status": "Unexpected error", "error": str(e)}
    finally:
        driver.quit()




def verify_user_shallow(registration_number, ums_password):
    
    try:
        driver = webdriver.Chrome(service=service)
        driver.get("https://ums.lpu.in/lpuums/LoginNew.aspx")


        for attempt in range(3):
            try:
                reg_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "txtU"))
                )
                reg_field.clear()
                reg_field.send_keys(registration_number)
                break
            except StaleElementReferenceException:
                time.sleep(1)


        for attempt in range(3):
            try:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "TxtpwdAutoId_8767"))
                )
                password_field.clear()
                password_field.send_keys(ums_password)
                break
            except StaleElementReferenceException:
                time.sleep(1)

    
        for attempt in range(3):
            try:
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "iBtnLogins150203125"))
                )
                login_button.click()
                break
            except StaleElementReferenceException:
                time.sleep(1)


        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        if "Important Links and Information" in driver.page_source:
            return { "status": "Login Successful"}
        else:
            return {"status": "Invalid Details"}

    except StaleElementReferenceException:
        return {"status": "Stale element reference error"}
    except NoSuchElementException:
        return {"status": "Element not found"}
    except TimeoutException:
        return {"status": "Timeout error"}
    except Exception as e:
        return {"status": "Unexpected error", "error": str(e)}
    finally:
        driver.quit()