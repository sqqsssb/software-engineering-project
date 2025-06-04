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

        // 校验输入是否为空
        if (!userPrompt) {
            console.log("触发校验的调用栈:", new Error().stack); // 打印调用栈
            alert("请输入项目需求（Prompt）！");
            return; // 终止后续操作
        }

        // 2. 显示加载状态（可选，提升用户体验）
        $(this).text("执行中...").prop("disabled", true); // 禁用按钮并修改文本

        // 3. 发送 AJAX 请求到后端接口（假设接口为 /run_prompt）
        $.post("/run_prompt", { prompt: userPrompt })
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

// 添加阶段控制相关函数
function showPhaseControl() {
    const controlHtml = `
        <div class="phase-control">
            <h3>阶段控制</h3>
            <div class="control-buttons">
                <button onclick="continuePhase()" class="btn btn-primary">继续执行</button>
                <button onclick="showRestartDialog()" class="btn btn-warning">重新执行</button>
            </div>
        </div>
    `;
    $("#chat-box").append(controlHtml);
}

function continuePhase() {
    $.ajax({
        url: '/api/phase/control',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ action: 'continue' }),
        success: function(response) {
            if (response.status === 'success') {
                // 继续执行阶段
                console.log('Continuing phase execution');
            }
        },
        error: function(error) {
            console.error('Error continuing phase:', error);
        }
    });
}

function showRestartDialog() {
    const dialogHtml = `
        <div class="restart-dialog">
            <h4>重新执行阶段</h4>
            <textarea id="restartPrompt" placeholder="输入新的提示（可选）"></textarea>
            <div class="dialog-buttons">
                <button onclick="restartPhase()" class="btn btn-warning">确认重启</button>
                <button onclick="closeRestartDialog()" class="btn btn-secondary">取消</button>
            </div>
        </div>
    `;
    $("#chat-box").append(dialogHtml);
}

function closeRestartDialog() {
    $(".restart-dialog").remove();
}

function restartPhase() {
    const restartPrompt = $("#restartPrompt").val();
    $.ajax({
        url: '/api/phase/control',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            action: 'restart',
            restart_prompt: restartPrompt
        }),
        success: function(response) {
            if (response.status === 'success') {
                closeRestartDialog();
                console.log('Phase will be restarted');
            }
        },
        error: function(error) {
            console.error('Error restarting phase:', error);
        }
    });
}

// 定期检查阶段状态
function checkPhaseState() {
    $.getJSON("/api/phase/state", function(response) {
        if (response.status === 'success') {
            const phaseState = response.phase_state;
            if (phaseState.is_completed) {
                showPhaseControl();
            }
        }
    });
}

// 每5秒检查一次阶段状态
setInterval(checkPhaseState, 5000);

// 获取DOM元素
const messagesContainer = document.getElementById('messages');
const promptInput = document.getElementById('prompt');
const sendButton = document.getElementById('send');
const phaseState = document.getElementById('phase-state');
const continueButton = document.getElementById('continue-phase');
const restartButton = document.getElementById('restart-phase');
const restartPromptContainer = document.querySelector('.restart-prompt');
const restartPromptInput = document.getElementById('restart-prompt-input');

// 获取消息历史
async function fetchMessages() {
    try {
        const response = await fetch('/get_messages');
        const messages = await response.json();
        displayMessages(messages);
    } catch (error) {
        console.error('Error fetching messages:', error);
    }
}

// 显示消息
function displayMessages(messages) {
    messagesContainer.innerHTML = '';
    messages.forEach(message => {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.role.toLowerCase()}`;
        messageElement.innerHTML = `
            <strong>${message.role}:</strong>
            <p>${message.text}</p>
        `;
        messagesContainer.appendChild(messageElement);
    });
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// 发送消息
async function sendMessage() {
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const formData = new FormData();
    formData.append('prompt', prompt);

    try {
        const response = await fetch('/run_prompt', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            promptInput.value = '';
            fetchMessages();
        } else {
            console.error('Error:', result.message);
        }
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

// 获取阶段状态
async function fetchPhaseState() {
    try {
        const response = await fetch('/api/phase/state');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayPhaseState(data.phase_state);
        }
    } catch (error) {
        console.error('Error fetching phase state:', error);
    }
}

// 显示阶段状态
function displayPhaseState(state) {
    phaseState.innerHTML = `
        <p><strong>任务提示:</strong> ${state.task_prompt || '无'}</p>
        <p><strong>当前回合:</strong> ${state.current_turn || 0}</p>
        <p><strong>是否完成:</strong> ${state.is_completed ? '是' : '否'}</p>
        <p><strong>需要重启:</strong> ${state.needs_restart ? '是' : '否'}</p>
    `;
}

// 继续执行阶段
async function continuePhase() {
    try {
        const response = await fetch('/api/phase/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: 'continue' })
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            fetchPhaseState();
            fetchMessages();
        }
    } catch (error) {
        console.error('Error continuing phase:', error);
    }
}

// 重新执行阶段
async function restartPhase() {
    const restartPrompt = restartPromptInput.value.trim();
    try {
        const response = await fetch('/api/phase/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'restart',
                restart_prompt: restartPrompt
            })
        });
        const result = await response.json();
        
        if (result.status === 'success') {
            restartPromptInput.value = '';
            restartPromptContainer.style.display = 'none';
            fetchPhaseState();
            fetchMessages();
        }
    } catch (error) {
        console.error('Error restarting phase:', error);
    }
}

// 事件监听器
sendButton.addEventListener('click', sendMessage);
promptInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

continueButton.addEventListener('click', continuePhase);
restartButton.addEventListener('click', () => {
    restartPromptContainer.style.display = 
        restartPromptContainer.style.display === 'none' ? 'block' : 'none';
});

// 定期更新消息和阶段状态
setInterval(fetchMessages, 1000);
setInterval(fetchPhaseState, 1000);

// 初始加载
fetchMessages();
fetchPhaseState();


