import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import mysql.connector 
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re


st.set_page_config(
                   layout="wide", 
                   page_title= "BizCardX: Extracting Business Card Data with OCR",
                   page_icon= "card-text",
                   initial_sidebar_state= "expanded",
)

mithun=mysql.connector.connect(host='localhost',user='root',password='Nuhtim25*',database='bizcardx')
suresh=mithun.cursor()


selected = option_menu(menu_title="BizCardX: Extracting Business Card Data with OCR",
                           options=["Home","Upload & Extract","Modify"], 
                           menu_icon="card-text",
                           icons=["house","cloud-upload","pencil-square"],
                           default_index=0,
                           orientation="horizontal",

)
reader = easyocr.Reader(['en'])

# HOME MENU
if selected == "Home":
    col1,col2 = st.columns(2)
    with col1:
        st.image(Image.open("C:/Users/91915/Downloads/home_ocr.jpg"),width = 500)        
    with col2:
        st.title(':violet[BizCardX: Extracting Business Card Data with OCR]')
        st.subheader(':violet[Technologies Used]:')
        st.write('Python,easy OCR, Streamlit, SQL, Pandas.')
        st.subheader(':violet[Overview]:')
        st.write('In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.')
        st.markdown("## :violet[Done by] : MITHUN S")
        st.markdown("[Githublink](https://github.com/Mithun250/Phonepe_pulse)")
    st.write("---")  


# UPLOAD AND EXTRACT MENU
if selected == "Upload & Extract":
    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader("upload here",label_visibility="collapsed",type=["png","jpeg","jpg"])
    

    if not os.path.exists("uploaded_cards"):
        os.makedirs("uploaded_cards")

    if uploaded_card is not None:
    
        with open(os.path.join("uploaded_cards",uploaded_card.name), "wb") as f:
            f.write(uploaded_card.getbuffer())   


        def image_preview(image,res): 
            for (bbox, text,prob) in res: 
              # unpack the bounding box
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15,15)
            plt.axis('off')
            plt.imshow(image)
        
        # DISPLAYING THE UPLOADED CARD
        col1,col2 = st.columns(2,gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("### You have uploaded the card")
            st.image(uploaded_card)
        # DISPLAYING THE CARD WITH HIGHLIGHTS
        with col2:
            st.markdown("#     ")
            st.markdown("#     ")
            with st.spinner("Please wait processing image..."):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("### Image Processed and Data Extracted")
                st.pyplot(image_preview(image,res))  
                
            
        #easy OCR
        saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
        result = reader.readtext(saved_img,detail = 0,paragraph=False)
        
        # CONVERTING IMAGE TO BINARY TO UPLOAD TO SQL DATABASE
        def img_to_binary(file):
            # Convert image data to binary format
            with open(file, 'rb') as file:
                binaryData = file.read()
            return binaryData
        
        data = {"company_name" : [],
                "card_holder" : [],
                "designation" : [],
                "mobile_number" :[],
                "email" : [],
                "website" : [],
                "area" : [],
                "city" : [],
                "state" : [],
                "pin_code" : [],
                "image" : img_to_binary(saved_img)
               }

        def get_data(res):
            for ind,i in enumerate(res):

                # To get WEBSITE_URL
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] +"." + res[5]

                # To get EMAIL ID
                elif "@" in i:
                    data["email"].append(i)

                # To get MOBILE NUMBER
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) ==2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                # To get COMPANY NAME  
                elif ind == len(res)-1:
                    data["company_name"].append(i)

                # To get CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)

                # To get DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+',i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+',i):
                    data["area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*',i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                if state_match:
                     data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                    data["state"].append(i.split()[-1])
                if len(data["state"])== 2:
                    data["state"].pop(0)

                # To get PINCODE        
                if len(i)>=6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["pin_code"].append(i[10:])
        get_data(result)
        
        #FUNCTION TO CREATE DATAFRAME
        def create_df(data):
            df = pd.DataFrame(data)
            return df
        df = create_df(data)
        st.success("### Data Extracted!")
        st.write(df)
        
        if st.button("Upload to Database"):
            for i,row in df.iterrows():
                sql = """INSERT INTO business_cards(CompanyName, CardHolder, Designation, MobileNumber, Email, Website, Area, City, State, PinCode, Image)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                suresh.execute(sql, tuple(row))
                mithun.commit()
            st.success("#### Uploaded to database successfully!") 

# MODIFY MENU    
if selected == "Modify":
    col1,col2,col3 = st.columns([3,3,2])
    col2.markdown("## Modify or Delete the data here")
    column1,column2 = st.columns(2,gap="large")
    try:
        with column1:
            suresh.execute("SELECT CardHolder FROM business_cards")
            result = suresh.fetchall()
            cards = {}
            for row in result:
                cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(cards.keys()))
            st.markdown("#### Update or modify any data below")
            sql = """SELECT CompanyName, CardHolder, Designation, MobileNumber, Email, Website, Area, City, State, PinCode
                    FROM business_cards WHERE CardHolder = %s"""

            suresh.execute(sql, (selected_card,))
            result = suresh.fetchone()


             # DISPLAYING ALL THE INFORMATIONS
            CompanyName = st.text_input("CompanyName", result[0])
            CardHolder = st.text_input("CardHolder", result[1])
            Designation = st.text_input("Designation", result[2])
            MobileNumber = st.text_input("MobileNumber", result[3])
            Email = st.text_input("Email", result[4]) 
            Website = st.text_input("Website", result[5])
            Area = st.text_input("Area", result[6])
            City = st.text_input("City", result[7])
            State = st.text_input("State", result[8])
            PinCode = st.text_input("PinCode", result[9])

            if st.button("Commit changes to DB"):
                # Update the information for the selected business card in the database
                suresh.execute("""UPDATE business_cards
                                SET CompanyName=%s, CardHolder=%s, Designation=%s, MobileNumber=%s, Email=%s, Website=%s, Area=%s, City=%s, State=%s, PinCode=%s
                                WHERE CardHolder=%s""", (CompanyName, CardHolder, Designation, MobileNumber, Email, Website, Area, City, State, PinCode, selected_card))

                mithun.commit() 
                st.success("Information updated in database successfully.")

        with column2:
            suresh.execute("SELECT CardHolder FROM business_cards")
            result = suresh.fetchall()
            cards = {}
            for row in result:
               cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            if st.button("Yes Delete Business Card"):
                suresh.execute(f"DELETE FROM business_cards WHERE CardHolder='{selected_card}'")
                mithun.commit()
                st.success("Business card information deleted from database.")

    except:
        st.warning("There is no data available in the database")

