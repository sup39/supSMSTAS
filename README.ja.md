# supSMSTAS
<p align="center">
  <a href="https://github.com/sup39/supSMSTAS/blob/main/README.md">English</a> |
  <span>日本語</span>
</p>

*A tool to **sup**port **S**uper **M**ario **S**unshine **T**ool **A**ssisted **S**peedrun/Superplay*  
サンシャインTASをサポートするためのツール

## インストール
cmd.exeなどで次の命令を実行します：
```
pip install supSMSTAS
```
:warning: Python 3.8以上が必要です

## 使い方
cmd.exeなどで次の命令を実行すればsupSMSTASが起動します：
```
python -m supSMSTAS
```

## 必要なGeckoコード
次のコードをDolphinに追加し、有効にする必要があります：
```
C20ECDE0 00000004
3C60817F 80631000
7C631B79 38600258
41820008 38600096
60000000 00000000
C20ED284 00000005
4E800021 3D60817F
816B1010 55608380
2800817E 4082000C
7D6803A6 4E800021
60000000 00000000
```

QF syncを弄るコードや地形三角形・判定を描画するコードを使っている場合、無効にしておく必要があります。

もしRuntimeタブのチェックボックスが正常に動作しない場合、(上記のGeckoコードを除いて)Dolphinに追加した全てのGeckoコードを無効にしてみてください。

## ソースコードを直接に実行する方法
dependenciesをインストールするために、一番簡単な方法はソースコードのルートディレクトリで次のコマンドを実行することです：
```
pip install .
```

Pythonのmodule/scriptの問題により、プログラムを実行するために、`python path/to/supSMSTAS/__main__.py`(scriptとして)の代わりに、`src/supSMSTAS/`ディレクトリの外で`python -m path.to.supSMSTAS`(moduleとして)を実行してください。例えば、`src/`ディレクトリで次のコマンドを実行します：
```
python -m supSMSTAS
```
