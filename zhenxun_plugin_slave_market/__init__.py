from nonebot import require
from nonebot.plugin.on import on_command
from nonebot.adapters.onebot.v11 import (
    GROUP,
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
    )

import nonebot
import os
import random
import asyncio
import time
from models.bag_user import BagUser
from models.group_member_info import GroupInfoUser
from datetime import datetime,date,timedelta
import pytz
from nonebot import require
require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender import md_to_pic
from .model import UsersInfo,BayUsers
from .utils import *

__zx_plugin_name__ = "群友市场"
__plugin_usage__ = """
usage:
    发送群友市场 查看群友交易市场，
    发送购买群友+@群友 可买下群友帮你打工
    发送我的群友查看 我当前已经购买的群友，
    发送一键打工 可让你的所有群友为你打工（没有群友就自己打工）
    发送市场税率 查看真寻的税率
    为规范劳动市场（捞油水），群友所执行的每一笔交易与打工真寻都会收税，税率请发送"市场税率"查看
        
""".strip()
__plugin_des__ = "群友交易市场"
__plugin_cmd__ = ["群友市场", "购买群友","市场税率"]
__plugin_type__ = ("群内小游戏",)
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": __plugin_cmd__,
}
today = date.today()

usershop = on_command("群友市场",aliases = {"查看群友市场"}, permission=GROUP, priority = 5, block = True)

@usershop.handle()
async def _(bot:Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.user_id
    ulist:dict[int, int]={}
    ulist = await UsersInfo.get_all_user(group_id)
    if ulist:
        msg=f'### 群友市场（未出现在市场里的都只值100）\n' \
            '|名称|qq号|身价|主人|\n' \
            '| --- | --- | --- | --- |\n'
        for qq,p in ulist.items():
            if user_ := await GroupInfoUser.get_or_none(user_qq=qq, group_id=group_id):
                user_name = user_.user_name
            if user_ := await BayUsers.get_or_none(group_id=group_id,auser_qq=qq):
                if usern := await GroupInfoUser.get_or_none(user_qq=user_.muser_qq, group_id=group_id):
                    user_name1 = usern.user_name
                umaster = user_name1
                msg += f"|<img width='20%' src='http://q1.qlogo.cn/g?b=qq&nk={qq}&s=100'/>  {user_name}|{qq}|{p}|<img width='20%' src='http://q1.qlogo.cn/g?b=qq&nk={usern.user_qq}&s=100'/>  {umaster}|\n"
            else:
                umaster="无"
                msg += f"|<img width='20%' src='http://q1.qlogo.cn/g?b=qq&nk={qq}&s=100'/>  {user_name}|{qq}|{p}|{umaster}|\n"

        output = await md_to_pic(md=msg)
        await usershop.finish(MessageSegment.image(output), at_sender=True)
    else:
        await usershop.finish("群友市场空无一人（所有人都只值100）", at_sender=True)



myuser = on_command("我的群友",aliases = {"查看我的群友"} , permission = GROUP, priority = 5, block = True)

@myuser.handle()
async def _(bot:Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.user_id
    ulist:dict[int, int]={}
    ulist = await UsersInfo.get_all_auser(user_id,group_id)
    if ulist:
        msg=f'### 我的群友\n' \
            '|名称|qq号|身价|\n' \
            '| --- | --- | --- |\n'
        for qq,p in ulist.items():
            if user_ := await GroupInfoUser.get_or_none(user_qq=qq, group_id=group_id):
                user_name = user_.user_name
            msg += f"|<img width='20%' src='http://q1.qlogo.cn/g?b=qq&nk={qq}&s=100'/>  {user_name}|{qq}|{p}|\n"

        output = await md_to_pic(md=msg)
        await myuser.finish(MessageSegment.image(output), at_sender=True)
    else:
        await myuser.finish("你还没有购买群友", at_sender=True)

# 查看娶群友卡池

buyuser = on_command("购买群友", permission = GROUP, priority = 5, block = True)

@buyuser.handle()
async def _(bot:Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.user_id
    at = get_message_at(event.json())
    try:
        if user_ := await GroupInfoUser.get_or_none(user_qq=at[0], group_id=group_id):
            user_name = user_.user_name
    except:
        await buyuser.finish("不可以购买我捏~", at_sender=True)
        return   
    if at[0] == user_id:
        await buyuser.finish("不可以购买自己捏~", at_sender=True)
        return  
    user = await BayUsers.get_or_none(group_id=group_id,auser_qq=at[0])
    if not user:
        #第一次被买，钱给黑奴
        if await BagUser.get_gold(user_id,group_id)<100:
            await buyuser.finish(f"你买不起！需要{auser.body_price + tax(auser.body_price)}金币", at_sender=True)
            return
        m = await UsersInfo.add_user(user_id,group_id,at[0])
        a_tax_s=m + tax(m)
        a_tax_a=m - tax(m)
        await BagUser.add_gold(at[0],group_id,a_tax_a)
        await BagUser.spend_gold(user_id,group_id,a_tax_s)
        a = await BagUser.get_gold(at[0],group_id)
        u = await BagUser.get_gold(user_id,group_id)
        msg=f"成功购买了{user_name}！花费了{a_tax_s}金币，还剩{u}金币\n{user_name}获得了{a_tax_a}金币，现在拥有{a}金币，身价上涨{m}->{m+20}\n真寻酱共收了{str(tax(m))}金币的税"
        output = text_to_png(msg)
        await buyuser.finish(MessageSegment.image(output), at_sender=True)
    else:
        #被买走，钱给前主人
        auser = await UsersInfo.get_or_none(group_id=group_id,user_qq=at[0])
        if await BagUser.get_gold(user_id,group_id) < auser.body_price:
            await buyuser.finish(f"你买不起！需要{auser.body_price + tax(auser.body_price)}金币", at_sender=True)
            return
        if user_ := await GroupInfoUser.get_or_none(user_qq=user.muser_qq, group_id=group_id):
            user_name2 = user_.user_name
        m = await UsersInfo.add_user(user_id,group_id,at[0])
        a_tax_s=m + tax(m)
        a_tax_a=m - tax(m)
        if not m:
            await buyuser.finish("你已经是他的主人了！", at_sender=True)
            return
        else:
            if i := await UsersInfo.remove_user(user.muser_qq,group_id,at[0]):
                await BagUser.add_gold(user.muser_qq,group_id,a_tax_a)
                await BagUser.spend_gold(user_id,group_id,a_tax_s)
                await BagUser.add_gold(at[0],group_id,tax(m)/2)
                a = await BagUser.get_gold(at[0],group_id)
                u = await BagUser.get_gold(user_id,group_id)
                u2 = await BagUser.get_gold(user.muser_qq,group_id)
                msg=f"成功从{user_name2}那里购买了{user_name}！花费了{a_tax_s}金币，还剩{u}金币\n{user_name2}获得了{a_tax_a}金币，现在拥有{u2}金币\n{user_name}额外获得了{tax(m)/2}金币，现在拥有{a}金币，身价上涨{m}->{m+20}\n真寻酱共收了{str(tax(m))}金币的税"
                output = text_to_png(msg)
                await buyuser.finish(MessageSegment.image(output), at_sender=True)

work = on_command("一键打工", permission = GROUP, priority = 5, block = True)

@work.handle()
async def _(bot:Bot, event: GroupMessageEvent):
    present = datetime.now(pytz.timezone('Asia/Shanghai'))
    group_id = event.group_id
    user_id = event.user_id
    user, is_create = await UsersInfo.get_or_create(user_qq=user_id, group_id=group_id)
    print(user.checkin_time_last)
    print(present)
    if user.checkin_time_last + timedelta(hours=3) >= present:
        await work.finish("最近三小时内已经打过工了!", at_sender=True)
        return
    ulist = await UsersInfo.get_all_auser(user_id,group_id)
    if not ulist:
        #没有黑奴，只能自己去打工
        await UsersInfo.work(user_id,group_id)
        gold = random.randint(10, 40)
        m = await UsersInfo.get_or_none(user_qq=user_id, group_id=group_id)
        gold=gold+ random.randint(m.body_price/10, m.body_price/5)
        glod_after_tax=gold - tax(gold)
        await BagUser.add_gold(user_id,group_id,gold)
        u = await BagUser.get_gold(user_id,group_id)
        NICKNAME="【你】"
        msg=(
            random.choice(
                [
                    f"{NICKNAME}参加了网红主播的不要笑挑战。获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}在闲鱼上卖东西，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}去在大街上发小传单，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}参加漫展，帮著名画师毛玉牛乳兜售新作，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}在美食街出售鸡你太美飞饼，虽然把饼甩飞了，但是围观群众纷纷购买鸡哥飞饼，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}偷渡到美国在中餐馆洗盘子，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}去黑煤窑挖煤，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}去横店当太君群演，被八路手撕了20次导演才说咔，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}去参加银趴服务别人，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}去拍摄小电影，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                    f"{NICKNAME}去b站做审核员，看了十二小时旋转鸡块，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                ]
            )
        )
        msg=msg+f"\n当前共有{u}金币"
        msg="你没有群友只能自己去打工\n"+msg
        output = text_to_png(msg)
        await work.finish(MessageSegment.image(output), at_sender=True)
    else:
        #派出所有黑奴去干活
        await UsersInfo.work(user_id,group_id)
        golds=0
        msgs="你派出了所有群友去打工\n"
        for qq,p in ulist.items():
            if user_ := await GroupInfoUser.get_or_none(user_qq=qq, group_id=group_id):
                NICKNAME = f"【{user_.user_name}】"
            gold = random.randint(10, 40)
            gold=gold+ random.randint(p/10, p/5)
            glod_after_tax=gold - tax(gold)
            #10%概率没钱
            ran=random.randint(1,10)
            if ran != 6:
                msg=(
                    random.choice(
                        [
                            f"{NICKNAME}参加了网红主播的不要笑挑战。获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}在闲鱼上卖东西，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}去在大街上发小传单，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}参加漫展，帮著名画师毛玉牛乳兜售新作，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}在美食街出售鸡你太美飞饼，虽然把饼甩飞了，但是围观群众纷纷购买鸡哥飞饼，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}偷渡到美国在中餐馆洗盘子，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}去黑煤窑挖煤，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}去横店当太君群演，被八路手撕了20次导演才说咔，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}去参加银趴服务别人，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}去拍摄小电影，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                            f"{NICKNAME}去b站做审核员，看了十二小时旋转鸡块，获得收入{str(glod_after_tax)}金币,真寻酱收了{str(tax(gold))}金币的税",
                        ]
                    )
                )
                golds=golds+glod_after_tax
            else:
                msg=(
                    random.choice(
                        [
                            f"{NICKNAME}参加了网红主播的不要笑挑战。结果刚上场就蚌不住了，一分没挣着",
                            f"{NICKNAME}在闲鱼上卖东西，结果完全卖不出去，一分没挣着",
                            f"{NICKNAME}去在大街上发小传单，没有一个人要传单，一分没挣着",
                            f"{NICKNAME}参加漫展，帮著名画师毛玉牛乳兜售新作，结果忍不住在展台冲了出来，被人家赶了出去，一分没挣着",
                            f"{NICKNAME}在美食街出售鸡你太美飞饼，结果把饼甩飞了，围观群众都散了，一分没挣着",
                            f"{NICKNAME}偷渡到美国在中餐馆洗盘子，结果一个黑人逃进了中餐馆，后面一个警察在后面追着扫射，{NICKNAME}害怕的跑了出来，一分没挣着",
                            f"{NICKNAME}去黑煤窑挖煤，但{NICKNAME}没有力气完全挖不动，一分没挣着还被骂了",
                            f"{NICKNAME}去横店当太君群演，被八路手撕了20次导演还说不行，说{NICKNAME}演的不好就把你赶出去了，一分没挣着",
                            f"{NICKNAME}去参加银趴服务别人，别人说{NICKNAME}把他弄疼了，就把{NICKNAME}赶出去了，一分没挣着还被骂了",
                            f"{NICKNAME}去拍摄小电影，因为没有经验某些姿势老做不好,把{NICKNAME}赶了出去，一分没挣着还被骂了"
                            f"{NICKNAME}去b站做审核员，要看十二小时旋转鸡块，{NICKNAME}以为没事随便看两眼就给过了，结果被举报中间掺了毛玉牛乳最新画作，一分没挣着被开除了",
                        ]
                    )
                )                
            msgs=msgs+msg+"\n"
        await BagUser.add_gold(user_id,group_id,golds)
        u = await BagUser.get_gold(user_id,group_id)
        msgs=msgs+f"你总共获取{golds}金币，当前共有{u}金币"
        output = text_to_png(msgs)
        await work.finish(MessageSegment.image(output), at_sender=True)

# 市场税率查询
tax_rate = on_command("市场税率", aliases={"查询税率"}, permission=GROUP, priority=5, block=True)

@tax_rate.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    tax_table = [
        {"区段": "0-1000", "税率": "1%"},
        {"区段": "1001-2000", "税率": "2.5%"},
        {"区段": "2001-5000", "税率": "4%"},
        {"区段": "5000以上", "税率": "6%"},
    ]
    msg = "### 市场税率\n\n"
    msg += "| 区段 | 税率 |\n"
    msg += "| --- | --- |\n"
    for row in tax_table:
        msg += f"| {row['区段']} | {row['税率']} |\n"
    output = await md_to_pic(md=msg)
    await tax_rate.finish(MessageSegment.image(output), at_sender=True)

def tax(price):
    tax_rate = [0.01, 0.025, 0.04, 0.06]
    if 0 <= price <= 1000:
        tax = price * tax_rate[0]
        return tax
    if 1000 < price <= 2000:
        tax = (price - 1000) * tax_rate[1] + tax_rate[0] * 1000
        return tax
    if 2000 < price <= 5000:
        tax = (price - 2000) * tax_rate[2] + tax_rate[0] * 1000 + tax_rate[1] * 1000
        return tax
    if price > 5000:
        tax = (price - 5000) * tax_rate[3] + tax_rate[0] * 1000 + tax_rate[1] * 1000 + tax_rate[2] * 3000
        return tax
