Chuyển động trong thư mục này được "nướng" từ CMU Graphics Lab Motion Capture Database
(mocap.cs.cmu.edu, bản BVH chuyển đổi bởi Bruce Hahne). Dữ liệu được phép dùng tự do,
kể cả thương mại, theo điều khoản của CMU; trích nguồn: "The data used in this project was
obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217."
walk.json  <- 07_01 (walk)
sneak.json <- 17_03 (walk stealthily)
Tạo lại: cd app && python -m engine.mascot.bake <file.bvh> <tên> <giây bắt đầu>
