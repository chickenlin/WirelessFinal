# WirelessFinal
110 Wireless Communication final project

[注意事項]Version.2和3需要使用到Version.1中的packer(完整的指令教學我之後再補)

[來源]這支程式碼是base[這支code](https://github.com/raspberrypi-tw/lora-sx1276/)

## Version.1

### 架構圖
目前只有考慮 uplink 部分，uplink 通過兩種不同頻率將訊號傳送給兩個路徑不同的 Gateway，Gateway 再將訊號傳至 Ethernet。

![](https://i.imgur.com/wOfTD5s.png)

### 程式架構
* uplink 程式碼部分請參考 [git](https://github.com/raspberrypi-tw/lora-sx1276/tree/master/04-gateway)。

* tx_forward.py 是 UE 透過天線 uplink 到 gateway 的程式，流程圖如下。

![](https://i.imgur.com/dvcYkAv.png)

* gw_rx.py 是 gateway 接收並推送到 Ethernet 的程式，流程圖如下。

![](https://i.imgur.com/4ZYywN3.png)

## Version.2
* 加入了判斷source和destination的功能，因為原本的lora天線是broadcast出去的，這裡我們在payload的前端加上了target，讓節點判斷這個封包是不是自己的

### 架構圖

![](https://i.imgur.com/P0ggZqw.png)

## Path 1(Lora 868MHz)
* tx.py流程圖
![](https://i.imgur.com/qGCVgn6.png)

* gw_forward.py流程圖
![](https://i.imgur.com/ZISE1aj.png)

* rx.py流程
![](https://i.imgur.com/SSmqX8m.png)

### 實驗步驟
* **步驟一**:tx.py送出資料
* **步驟二**:gw_forward.py確認資料，並且forward給下一個節點
  * 下一個節點可以為**gateway**或是**receiver**
* **步驟三**:rx.py確認資料
