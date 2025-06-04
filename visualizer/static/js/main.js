function append_message(role, text, avatarUrl) {
  
  var message_container = $("<div></div>").addClass("message-container");
  var avatar_element = $("<span></span>").addClass("avatar");
  var role_element = $("<p></p>").addClass("role").text(role);

  if (avatarUrl) {
    avatar_element.css("background-image", `url(${avatarUrl})`);
  } else {
    avatar_element.css("background-color", "green");
  }

  message_container.append(role_element);
  message_container.append(avatar_element);


  var parsedText = role === 'System' ? parseSystemMessage(text) : parseCodeBlocks(text, role);

  message_container.append(parsedText);

  var copyButton = $("<button></button>")
    .addClass("copy-button")
    .text("Copy")
    .click(function () {
      copyToClipboard(parsedText); // Call the copyToClipboard function
    });

  copyButton.click(function () {
    copyToClipboard(parsedText);
    copyButton.text("Copied"); 
    setTimeout(function () {
      copyButton.text("Copy"); 
    }, 5000); 
  });

  message_container.append(copyButton); // Append the copy button

  $("#chat-box").append(message_container);
}

function parseCodeBlocks(text, role) {
  var parts = text.split(/(```[\s\S]*?```)/g);
  var parsedText = $("<div></div>").addClass("message-text");
  parts.forEach(part => {
    if (part.startsWith("```") && role != "System") {
      var trimmedBlock = part.trim();
      var language = trimmedBlock.match(/^```(\w+)/);
      if (language) {
        language = language[1];
        var codeContent = trimmedBlock.replace(/^```(\w+)/, '').replace(/```$/, '');
        var codeBlockHTML = `
          <div class="code-block">
            <div class="code-block-header">${role} - ${language}</div>
            <pre class="language-${language} dark line-numbers" data-line><code>${hljs.highlightAuto(codeContent, [language]).value}</code></pre>
          </div>
        `;
        parsedText.append(codeBlockHTML);
      }
    } else {
      parsedText.append(marked(_.escape(part), {breaks: true}));
    }
  });
  return parsedText;
}


function get_new_messages() {

  $.getJSON("/get_messages", function (data) {
    var lastDisplayedMessageIndex = $("#chat-box .message-container").length;

    for (var i = lastDisplayedMessageIndex; i < data.length; i++) {
      var role = data[i].role;
      var text = data[i].text;
      var avatarUrl = data[i].avatarUrl;

      append_message(role, text, avatarUrl);

    }
  });
}

function parseSystemMessage(text) {
  var message = $("<div></div>").addClass("message-text").addClass("system-message");
  var firstLine = text.split('\n')[0];
  var collapsed = true;

  var messageContent = $("<div></div>").html(marked(firstLine, { breaks: true })).addClass("original-markdown");
  var originalMarkdown = $("<div></div>").html(marked(text, { breaks: true })).addClass("original-markdown");

  var expandButton = $("<button></button>")
    .addClass("expand-button")
    .text("Expand")
    .click(function () {
      if (collapsed) {
        messageContent.hide();
        originalMarkdown.show();
        expandButton.text("Collapse");
      } else {
        messageContent.show();
        originalMarkdown.hide();
        expandButton.text("Expand");
      }
      collapsed = !collapsed;
    });

  message.append(messageContent);
  message.append(originalMarkdown);
  message.append(expandButton);

  originalMarkdown.hide();

  return message;
}

function copyToClipboard(element) {
  // Create a temporary textarea element to hold the text
  var tempTextArea = document.createElement("textarea");
  tempTextArea.value = element.text();
  document.body.appendChild(tempTextArea);

  // Select and copy the text from the textarea
  tempTextArea.select();
  document.execCommand("copy");

  // Remove the temporary textarea
  document.body.removeChild(tempTextArea);
}



$(document).ready(function () {
    get_new_messages();
    setInterval(function () {
    get_new_messages();
    }, 1000);

    // 新增：Run 按钮点击事件
    $("#run-button").off("click").click(function(e) {
        e.preventDefault(); // 阻止默认行为（如果是表单按钮）
        const button = $(this);
        button.prop("disabled", true).text("Running...");  // 禁用并修改文本
        // 1. 获取用户输入的 Prompt
        const userPrompt = $("#user-prompt").val().trim();
        const userName = $("#user-name").val().trim();  // 新增：获取 name 输入框的值
        const userModel = $("#user-model").val().trim();  // 新增：获取 model 输入框的值
        const userPath = $("#user-path").val().trim();    // 新增：获取 path 输入框的值
        const userConfig = $("#user-config").val().trim();  // 新增：获取 config 输入框的值
        const userOrg = $("#user-org").val().trim();        // 新增：获取 org 输入框的值

        // 校验输入是否为空
        if (!userPrompt) {
            console.log("触发校验的调用栈:", new Error().stack); // 打印调用栈
            alert("请填写所有必填字段！");
            return; // 终止后续操作
        }

        // 2. 显示加载状态（可选，提升用户体验）
        $(this).text("执行中...").prop("disabled", true); // 禁用按钮并修改文本

        // 3. 发送 AJAX 请求到后端接口（假设接口为 /run_prompt）
        $.post("/run_prompt", { 
          prompt: userPrompt,
          name: userName, // 新增：发送 name 参数
          model: userModel,  // 新增：发送 model 参数
          path: userPath,     // 新增：发送 path 参数
          config: userConfig,  // 新增：发送 config 参数
          org: userOrg         // 新增：发送 org 参数
      })
            .done(function(response) {
                if (response.status === "success") {
                    // 后端执行成功：在聊天窗口添加系统提示
                    const systemMessage = "已接收需求：" + userPrompt + "\n正在生成项目...";
                    append_message("System", systemMessage, ""); // 角色为 System，无头像

                    // 清空输入框
                    $("#user-prompt").val("");
                } else {
                    // 后端执行失败：显示错误信息
                    alert("执行失败：" + response.message);
                }
            })
            .fail(function(xhr, status, error) {
                console.error("AJAX 请求失败", error);
                alert("网络请求失败，请重试！");
            })
            .always(function() {
                // 4. 恢复按钮状态
                $("#run-button").text("Run ChatDev").prop("disabled", false);
            });
    });
});


