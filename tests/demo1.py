from fastapi import FastAPI, BackgroundTasks
import time

app = FastAPI()

# 模拟一个耗时的“小任务”，比如发送邮件
def send_email(email: str, message: str):
    # 模拟发送过程
    time.sleep(2) 
    print(f"邮件已发送给 {email}: {message}")

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    """
    接口立即返回，邮件发送在后台进行
    """
    # 将任务添加到后台队列
    # 注意：这里不会等待 send_email 执行完毕，而是直接返回下面的响应
    background_tasks.add_task(send_email, email, "这是后台任务发送的内容")
    
    return {"message": f"通知任务已添加，邮件将发送至: {email}"}