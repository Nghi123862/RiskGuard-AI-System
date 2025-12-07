from passlib.context import CryptContext

# 1. Cấu hình thuật toán mã hóa
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Mật khẩu bạn muốn đặt
my_password = "admin123"

# 3. Tạo mã Hash
my_hash = pwd_context.hash(my_password)

print("\n" + "="*50)
print("ĐÂY LÀ MÃ MẬT KHẨU CỦA BẠN (COPY DÒNG DƯỚI):")
print(my_hash)
print("="*50 + "\n")