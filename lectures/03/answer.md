# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
    素のLLMでは最もらしい一般論で答えていたが、今回は用語集を参考にしたため、正しく答えられている。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
    search_glossary({'query': 'LoRA'})
    search_glossary({'query': 'QLoRA'})
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：
    ツールは glossary

    説明は、
    """指定した回の用語から1つを選び、
    確認問題と答えを返す。

    「第2回の確認問題を出して」のように、
    復習用の問題を求められたときに使う。
    """

## 宿題

- 取り組んだレベル：実装
- やったこと：
    app/tools.py に save_learning_log を追加
    学習記録を learning_log/ に個別のMarkdownファイルとして保存
    app/agent.py でツールに requires_approval=True を設定
    output_type に DeferredToolRequests を追加
    CLI で内容を表示して承認を尋ね、結果を渡してエージェントを再開
    tests/test_agent.py に承認・拒否と CLI 入力のテストを追加
- 結果：
    AIに渡す文章を"今日学んだことを保存して。内容: DeferredToolRequestsで承認待ちになり、DeferredToolResultsを渡してエージェントを再開できる。"のように内容付きで指示することで保存するかを問われ、承認すると保存されるようになった。
- 気づき・疑問：
    "今日学んだことを保存して"だけだとsearch_glossaryが呼び出されてしまった。
    この時に、学習内容を教えてもらいたいと言われるが、次に教えるときには別のプロンプトになり保存されない。