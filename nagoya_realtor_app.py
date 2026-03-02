#!/usr/bin/env python3
"""
名古屋不动产公司 - Streamlit 网页应用
部署: streamlit run app.py
或上传到 GitHub → streamlit.cloud 部署
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="名古屋不动产公司",
    page_icon="🏠",
    layout="wide"
)

# 缓存数据
@st.cache_data(ttl=3600)  # 缓存1小时
def scrape_suumo():
    """从SUUMO爬取"""
    url = "https://suumo.jp/kaisha/aichi/sa_nagoya/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    companies = []
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找公司信息 (根据实际结构调整)
        items = soup.select('div.cassettefly, div.searchobject')
        
        for item in items[:50]:
            name_elem = item.select_one('a')
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name and len(name) < 100:
                    companies.append({
                        'name': name,
                        'source': 'SUUMO'
                    })
                    
    except Exception as e:
        st.error(f"SUUMO 错误: {e}")
    
    return companies

@st.cache_data(ttl=3600)
def scrape_homes():
    """从HOMES爬取"""
    url = "https://www.homes.co.jp/realtor/aichi/nagoya-mcity/list/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    companies = []
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = soup.select('div.bdlItem, div.shopBox')
        
        for item in items[:50]:
            name = item.get_text(strip=True)
            if name and len(name) < 100:
                companies.append({
                    'name': name,
                    'source': 'HOMES'
                })
                
    except Exception as e:
        st.error(f"HOMES 错误: {e}")
    
    return companies

# 预设公司数据（网站爬不到时备用）
def get_preset_data():
    """预设数据"""
    return [
        {"name": "エイシン株式会社（My賃貸）", "phone": "0120-733-078", "source": "预设"},
        {"name": "株式会社部屋セレブ", "phone": "052-953-3388", "source": "预设"},
        {"name": "スタイルプラス株式会社", "phone": "052-265-6555", "source": "预设"},
        {"name": "株式会社賃貸住宅サービス", "phone": "052-957-2277", "source": "预设"},
        {"name": "株式会社エムホーム", "phone": "052-311-2155", "source": "预设"},
        {"name": "葵商事株式会社", "phone": "052-753-7555", "source": "预设"},
        {"name": "有限会社あさひ不動産", "phone": "052-731-5500", "source": "预设"},
        {"name": "株式会社サガ Realty", "phone": "052-771-7700", "source": "预设"},
    ]

def main():
    st.title("🏠 名古屋不动产公司")
    st.markdown("---")
    
    # 侧边栏
    st.sidebar.title("选项")
    refresh = st.sidebar.button("🔄 刷新数据")
    
    # 显示更新时间
    st.sidebar.markdown(f"**更新时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📋 公司列表", "🔍 搜索", "📊 统计"])
    
    with tab1:
        st.header("不动产公司列表")
        
        # 尝试获取数据
        companies = []
        
        with st.spinner("正在获取数据..."):
            companies.extend(scrape_suumo())
            companies.extend(scrape_homes())
        
        # 如果没爬到数据，用预设
        if not companies:
            st.warning("网站数据获取失败，显示预设数据")
            companies = get_preset_data()
        else:
            # 添加预设数据
            companies.extend(get_preset_data())
        
        # 去重
        seen = set()
        unique = []
        for c in companies:
            key = c['name'][:15]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        
        # 显示表格
        df = pd.DataFrame(unique)
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # 下载按钮
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载 CSV",
            data=csv,
            file_name="nagoya_realtor.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.header("🔍 搜索公司")
        
        search = st.text_input("输入公司名或关键词")
        
        if search:
            results = [c for c in unique if search.lower() in c['name'].lower()]
            
            st.write(f"找到 {len(results)} 个结果:")
            
            for c in results:
                st.markdown(f"""
                **{c['name']}**
                - 来源: {c.get('source', 'N/A')}
                - 电话: {c.get('phone', 'N/A')}
                ---
                """)
        else:
            st.info("请输入搜索关键词")
    
    with tab3:
        st.header("📊 统计信息")
        
        if not unique:
            st.warning("暂无数据")
        else:
            # 统计来源
            sources = {}
            for c in unique:
                s = c.get('source', 'Unknown')
                sources[s] = sources.get(s, 0) + 1
            
            st.write("#### 来源统计")
            st.bar_chart(sources)
            
            st.write(f"**总计: {len(unique)} 家公司**")

if __name__ == "__main__":
    main()
