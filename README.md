# mzkgl

これはshadertoyのsound shader用のeditorです。
python + ellという構成になってます。
見た目はブラウザアプリです。リアルタイムコンパイルになっています。
コンパイルが成功した時にはリアルタイムでセーブします。
fork機能も付いています。ディレクトリで分類しているのですが、カテゴリーって言葉を使ってます。
そしてカテゴリー間のファイルの移動が出来るようにしてあります。
一応テスト済ですが念のためにfileのdownload機能を付けました。Playボタンを押すと音が鳴ります。
音はstreamなので時間の区切りが有りません。そこで時間の区間を設け、その時間をループし続けます。
スタート時間もあるのでデバックには便利に使えると思います。
機能はほとんどないので、ちょっと使えば雰囲気が解ると思います。

準備
pip install eel
pip install pyopengl
pip install pyaudio
これをインストールすれば動きます。

起動
python main.py

