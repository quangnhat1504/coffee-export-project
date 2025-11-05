#!/usr/bin/env python3
"""Script to update news section in index.html"""

# Read the file
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new news content
new_news_items = '''                    <!-- News Item 1 - Giá cà phê -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1447933601403-0c6688de566e?w=400&h=300&fit=crop" alt="Coffee beans price">
                            <div class="news-category technology">GIÁ CÀ PHÊ</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">Giá cà phê Robusta tăng mạnh lên 4.850 USD/tấn</h3>
                            <p class="news-item-desc">Giá cà phê Robusta trên sàn London tăng 2,3% trong tuần qua, đạt mức cao nhất trong 15 năm do lo ngại nguồn cung từ Việt Nam giảm.</p>
                            <span class="news-item-date">Nov 03, 2025</span>
                        </div>
                    </article>

                    <!-- News Item 2 - Xuất khẩu -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1578632292335-df3abbb0d586?w=400&h=300&fit=crop" alt="Coffee export">
                            <div class="news-category education">XUẤT KHẨU</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">Kim ngạch xuất khẩu 10 tháng đạt 4,8 tỷ USD</h3>
                            <p class="news-item-desc">Xuất khẩu cà phê Việt Nam 10 tháng đầu năm đạt 1,45 triệu tấn, trị giá 4,8 tỷ USD, tăng 14,2% về lượng và 38,5% về giá trị so với cùng kỳ.</p>
                            <span class="news-item-date">Nov 02, 2025</span>
                        </div>
                    </article>

                    <!-- News Item 3 - Dự báo mùa vụ -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=300&fit=crop" alt="Coffee farm">
                            <div class="news-category business">DỰ BÁO</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">Vụ cà phê 2025-2026 dự kiến đạt 1,7 triệu tấn</h3>
                            <p class="news-item-desc">Sản lượng cà phê niên vụ mới được dự báo giảm 10-15% do ảnh hưởng hạn hán kéo dài tại Tây Nguyên trong quý 1/2025.</p>
                            <span class="news-item-date">Oct 30, 2025</span>
                        </div>
                    </article>

                    <!-- News Item 4 - Thị trường trong nước -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1610889556528-9a770e32642f?w=400&h=300&fit=crop" alt="Coffee market">
                            <div class="news-category technology">THỊ TRƯỜNG</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">Giá cà phê nội địa tại Đắk Lắk đạt 128.000 đồng/kg</h3>
                            <p class="news-item-desc">Giá thu mua tại Tây Nguyên tiếp tục tăng mạnh, cao nhất ở Đắk Lắk 128.000 đ/kg, tăng 4.000 đ/kg so với tuần trước do hàng về ít.</p>
                            <span class="news-item-date">Oct 28, 2025</span>
                        </div>
                    </article>

                    <!-- News Item 5 - Chính sách -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400&h=300&fit=crop" alt="Coffee policy">
                            <div class="news-category business">CHÍNH SÁCH</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">Bộ NN&PTNT hỗ trợ 500 tỷ đồng tái canh cà phê</h3>
                            <p class="news-item-desc">Chương trình tái canh cải tạo vườn cà phê già cỗi với mục tiêu 50.000 ha tại Tây Nguyên, nâng cao năng suất và chất lượng.</p>
                            <span class="news-item-date">Oct 25, 2025</span>
                        </div>
                    </article>

                    <!-- News Item 6 - Công nghệ -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400&h=300&fit=crop" alt="Coffee technology">
                            <div class="news-category technology">CÔNG NGHỆ</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">Ứng dụng AI phân loại cà phê tại 20 nhà máy</h3>
                            <p class="news-item-desc">Hệ thống AI phân loại tự động giúp tăng 25% hiệu quả chế biến, đảm bảo chất lượng đồng đều cho xuất khẩu.</p>
                            <span class="news-item-date">Oct 22, 2025</span>
                        </div>
                    </article>

                    <!-- News Item 7 - Thị trường quốc tế -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1511920170033-f8396924c348?w=400&h=300&fit=crop" alt="International market">
                            <div class="news-category education">QUỐC TẾ</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">Đức tăng nhập khẩu cà phê Việt Nam 18%</h3>
                            <p class="news-item-desc">Thị trường Đức nhập khẩu 145.000 tấn cà phê Việt Nam trong 9 tháng đầu năm, trở thành thị trường EU lớn nhất.</p>
                            <span class="news-item-date">Oct 20, 2025</span>
                        </div>
                    </article>

                    <!-- News Item 8 - Bền vững -->
                    <article class="news-item">
                        <div class="news-thumbnail">
                            <img src="https://images.unsplash.com/photo-1587734195503-904fca47e0e9?w=400&h=300&fit=crop" alt="Sustainable coffee">
                            <div class="news-category business">BỀN VỮNG</div>
                        </div>
                        <div class="news-item-content">
                            <h3 class="news-item-title">5.000 ha cà phê được chứng nhận bền vững</h3>
                            <p class="news-item-desc">Các tỉnh Tây Nguyên triển khai mô hình canh tác cà phê bền vững theo tiêu chuẩn quốc tế Rainforest Alliance và UTZ.</p>
                            <span class="news-item-date">Oct 18, 2025</span>
                        </div>
                    </article>'''

# Find and replace the news list content
import re

# Pattern to match the news-list div and all its content
pattern = r'(<div class="news-list">).*?(</div>\s*</div>\s*</div>\s*</section>)'

# Replacement
replacement = r'\1\n' + new_news_items + r'\n                </div>\n            </div>\n        </div>\n    </section>'

# Perform replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back to file
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ News section updated successfully!")
print("🔄 Please refresh your browser to see the changes")
