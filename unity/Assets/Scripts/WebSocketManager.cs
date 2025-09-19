using UnityEngine;
using System;
using System.Collections;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

public class WebSocketManager : MonoBehaviour
{
    [Header("WebSocket Settings")]
    public string serverUrl = "ws://localhost:8000/api/animation/ws";
    public float reconnectInterval = 5f;
    public bool autoReconnect = true;
    
    private ClientWebSocket webSocket;
    private CancellationTokenSource cancellationTokenSource;
    private bool isConnecting = false;
    private bool isConnected = false;
    
    // Events
    public event Action<string> OnMessageReceived;
    public event Action OnConnected;
    public event Action OnDisconnected;
    public event Action<string> OnError;
    
    void Start()
    {
        ConnectToServer();
    }
    
    void OnDestroy()
    {
        DisconnectFromServer();
    }
    
    public async void ConnectToServer()
    {
        if (isConnecting || isConnected) return;
        
        isConnecting = true;
        
        try
        {
            webSocket = new ClientWebSocket();
            cancellationTokenSource = new CancellationTokenSource();
            
            var uri = new Uri(serverUrl);
            await webSocket.ConnectAsync(uri, cancellationTokenSource.Token);
            
            isConnected = true;
            isConnecting = false;
            OnConnected?.Invoke();
            
            Debug.Log("Connected to WebSocket server");
            
            // Start listening for messages
            StartCoroutine(ReceiveMessages());
        }
        catch (Exception e)
        {
            isConnecting = false;
            OnError?.Invoke($"Connection failed: {e.Message}");
            Debug.LogError($"WebSocket connection failed: {e.Message}");
            
            if (autoReconnect)
            {
                StartCoroutine(ReconnectAfterDelay());
            }
        }
    }
    
    public async void DisconnectFromServer()
    {
        if (webSocket != null)
        {
            isConnected = false;
            cancellationTokenSource?.Cancel();
            
            try
            {
                await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Disconnecting", CancellationToken.None);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"Error during WebSocket close: {e.Message}");
            }
            finally
            {
                webSocket.Dispose();
                webSocket = null;
                OnDisconnected?.Invoke();
            }
        }
    }
    
    public async void SendMessage(string message)
    {
        if (!isConnected || webSocket == null) return;
        
        try
        {
            var buffer = Encoding.UTF8.GetBytes(message);
            await webSocket.SendAsync(new ArraySegment<byte>(buffer), WebSocketMessageType.Text, true, cancellationTokenSource.Token);
        }
        catch (Exception e)
        {
            OnError?.Invoke($"Failed to send message: {e.Message}");
            Debug.LogError($"Failed to send WebSocket message: {e.Message}");
        }
    }
    
    private IEnumerator ReceiveMessages()
    {
        var buffer = new byte[4096];
        
        while (isConnected && webSocket != null)
        {
            try
            {
                var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationTokenSource.Token);
                
                if (result.MessageType == WebSocketMessageType.Text)
                {
                    var message = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    OnMessageReceived?.Invoke(message);
                }
                else if (result.MessageType == WebSocketMessageType.Close)
                {
                    Debug.Log("WebSocket connection closed by server");
                    break;
                }
            }
            catch (Exception e)
            {
                if (!cancellationTokenSource.Token.IsCancellationRequested)
                {
                    OnError?.Invoke($"Error receiving message: {e.Message}");
                    Debug.LogError($"WebSocket receive error: {e.Message}");
                    break;
                }
            }
            
            yield return null;
        }
        
        // Connection lost
        isConnected = false;
        OnDisconnected?.Invoke();
        
        if (autoReconnect)
        {
            StartCoroutine(ReconnectAfterDelay());
        }
    }
    
    private IEnumerator ReconnectAfterDelay()
    {
        yield return new WaitForSeconds(reconnectInterval);
        ConnectToServer();
    }
    
    public bool IsConnected()
    {
        return isConnected;
    }
    
    public void Reconnect()
    {
        DisconnectFromServer();
        ConnectToServer();
    }
    
    // Helper method to send animation data
    public void SendAnimationData(Dictionary<string, float> blendshapes, string emotion, List<string> gestures)
    {
        var animationData = new
        {
            type = "animation_update",
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
            blendshapes = blendshapes,
            emotion = emotion,
            gestures = gestures
        };
        
        string json = JsonUtility.ToJson(animationData);
        SendMessage(json);
    }
    
    // Helper method to trigger gesture
    public void TriggerGesture(string gestureType, float intensity = 1.0f)
    {
        var gestureData = new
        {
            type = "gesture_trigger",
            gesture_type = gestureType,
            intensity = intensity,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds()
        };
        
        string json = JsonUtility.ToJson(gestureData);
        SendMessage(json);
    }
} 