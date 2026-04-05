import requests
from bs4 import BeautifulSoup
import datetime
from deep_translator import GoogleTranslator
import json
import re

kst_time = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
date_str = kst_time.strftime("%Y%%2F%m%%2F%d") 

url = f"https://www.hanyang.ac.kr/web/www/re13?p_p_id=kr_ac_hanyang_cafe_web_portlet_CafePortlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_kr_ac_hanyang_cafe_web_portlet_CafePortlet_sMenuDate={date_str}&_kr_ac_hanyang_cafe_web_portlet_CafePortlet_action=view"

response = requests.get(url)
menu_data = []

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    meal_titles = soup.find_all('h3', class_='hyu-element')
    
    for title in meal_titles:
        title_text = title.get_text().strip()
        
        if "조식" in title_text or "중식" in title_text or "석식" in title_text:
            
            # 💡 핵심 수정: find_all_next() 대신 next_siblings를 사용합니다!
            # 이렇게 하면 문서 끝까지 가지 않고, 해당 구역 안에서만 찾습니다.
            for next_elem in title.next_siblings:
                
                # 다음 h3(예: 중식, 석식)를 만나거나, 구역이 끝나면 즉시 멈춥니다!
                if getattr(next_elem, 'name', None) == 'h3':
                    break
                    
                # <p> 태그를 찾으면 메뉴로 추출합니다.
                if getattr(next_elem, 'name', None) == 'p':
                    menu_text = next_elem.get_text().strip()
                    
                    if menu_text:
                        parts = menu_text.split('"')
                        
                        if len(parts) >= 3:
                            prefix = parts[0].strip()       
                            main_mixed = parts[1].strip()   
                            side_dishes = parts[2].strip()  
                            
                            eng_match = re.search(r'[a-zA-Z]', main_mixed)
                            if eng_match:
                                idx = eng_match.start()
                                kor_main = main_mixed[:idx].strip()  
                                eng_main = main_mixed[idx:].strip()  
                            else:
                                kor_main = main_mixed
                                eng_main = ""
                            
                            eng_sides = ""
                            if side_dishes:
                                try:
                                    eng_sides = GoogleTranslator(source='ko', target='en').translate(side_dishes)
                                except:
                                    eng_sides = "(Translation failed)"
                            
                            kor_full = f"{prefix} {kor_main} {side_dishes}".strip()
                            eng_full = f"{eng_main}, {eng_sides}".strip() if eng_main else eng_sides
                            
                            menu_data.append({
                                "type": title_text,
                                "kor": kor_full,
                                "eng": eng_full
                            })
                        else:
                            menu_data.append({
                                "type": title_text,
                                "kor": menu_text,
                                "eng": ""
                            })

with open('menu.json', 'w', encoding='utf-8') as f:
    json.dump(menu_data, f, ensure_ascii=False, indent=4)
    
print("menu.json 파일이 성공적으로 생성되었습니다!")
