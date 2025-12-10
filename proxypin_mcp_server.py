#!/usr/bin/env python3
"""ProxyPin MCP Server - 整合版"""
import os
import json
import requests
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP

# ProxyPin HTTP API配置
PROXYPIN_HOST = os.getenv("PROXYPIN_HOST", "127.0.0.1")
PROXYPIN_PORT = int(os.getenv("PROXYPIN_PORT", "17777"))
BASE_URL = f"http://{PROXYPIN_HOST}:{PROXYPIN_PORT}"
MESSAGES_URL = f"{BASE_URL}/messages"

# 创建Session，不使用系统代理
session = requests.Session()
session.trust_env = False
request_id_counter = 1

def call_proxypin_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
    """调用ProxyPin的MCP工具"""
    global request_id_counter
    
    if arguments is None:
        arguments = {}
    
    payload = {
        "jsonrpc": "2.0",
        "id": request_id_counter,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    request_id_counter += 1
    
    try:
        response = session.post(MESSAGES_URL, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "error" in result:
            raise Exception(f"MCP Error: {result['error']}")
        
        # 提取实际内容
        content = result.get("result", {}).get("content", [])
        if content:
            text = content[0].get("text", "{}")
            return json.loads(text)
        return {}
    except requests.exceptions.RequestException as e:
        raise Exception(f"ProxyPin连接失败: {e}")

mcp = FastMCP("ProxyPin")

@mcp.tool()
def search_requests(
    query: str = None, 
    method: str = None, 
    status_code: str = None,
    domain: str = None,
    header_search: str = None,
    request_body_search: str = None,
    response_body_search: str = None,
    min_duration: int = None,
    max_duration: int = None,
    limit: int = 20
):
    """高级搜索HTTP请求
    
    支持多种过滤条件：
    - query: URL关键词
    - method: HTTP方法(GET/POST等)
    - status_code: 状态码("200"或"2xx"范围)
    - domain: 域名过滤
    - header_search: 搜索请求/响应header
    - request_body_search: 搜索请求body(限1MB)
    - response_body_search: 搜索响应body(限1MB)
    - min_duration/max_duration: 响应时间范围(毫秒)
    """
    args = {"limit": limit}
    if query:
        args["query"] = query
    if method:
        args["method"] = method
    if status_code:
        args["status_code"] = status_code
    if domain:
        args["domain"] = domain
    if header_search:
        args["header_search"] = header_search
    if request_body_search:
        args["request_body_search"] = request_body_search
    if response_body_search:
        args["response_body_search"] = response_body_search
    if min_duration is not None:
        args["min_duration"] = min_duration
    if max_duration is not None:
        args["max_duration"] = max_duration
    return call_proxypin_tool("search_requests", args)

@mcp.tool()
def get_request_details(request_id: str):
    """获取请求详情"""
    return call_proxypin_tool("get_request_details", {"request_id": request_id})

@mcp.tool()
def replay_request(request_id: str):
    """重放请求"""
    return call_proxypin_tool("replay_request", {"request_id": request_id})

@mcp.tool()
def generate_code(request_id: str, language: str = "python"):
    """生成代码(python/js/curl)"""
    return call_proxypin_tool("generate_code", {"request_id": request_id, "language": language})

@mcp.tool()
def get_curl(request_id: str):
    """生成cURL命令"""
    return call_proxypin_tool("get_curl", {"request_id": request_id})

@mcp.tool()
def block_url(url_pattern: str, block_type: str = "blockRequest"):
    """屏蔽URL"""
    return call_proxypin_tool("block_url", {"url_pattern": url_pattern, "block_type": block_type})

@mcp.tool()
def add_response_rewrite(url_pattern: str, rewrite_type: str, value: str, key: str = None):
    """添加响应重写规则"""
    args = {"url_pattern": url_pattern, "rewrite_type": rewrite_type, "value": value}
    if key:
        args["key"] = key
    return call_proxypin_tool("add_response_rewrite", args)

@mcp.tool()
def add_request_rewrite(url_pattern: str, rewrite_type: str, key: str, value: str):
    """添加请求重写规则"""
    return call_proxypin_tool("add_request_rewrite", {
        "url_pattern": url_pattern,
        "rewrite_type": rewrite_type,
        "key": key,
        "value": value
    })

@mcp.tool()
def update_script(name: str, url_pattern: str, script_content: str):
    """创建或更新JavaScript脚本"""
    return call_proxypin_tool("update_script", {
        "name": name,
        "url_pattern": url_pattern,
        "script_content": script_content
    })

@mcp.tool()
def get_scripts():
    """获取所有脚本"""
    return call_proxypin_tool("get_scripts")

@mcp.tool()
def set_config(system_proxy: bool = None, ssl_capture: bool = None):
    """设置ProxyPin配置"""
    args = {}
    if system_proxy is not None:
        args["system_proxy"] = system_proxy
    if ssl_capture is not None:
        args["ssl_capture"] = ssl_capture
    return call_proxypin_tool("set_config", args)

@mcp.tool()
def add_host_mapping(domain: str, ip: str):
    """添加Hosts映射"""
    return call_proxypin_tool("add_host_mapping", {"domain": domain, "ip": ip})

@mcp.tool()
def get_proxy_status():
    """获取代理状态"""
    return call_proxypin_tool("get_proxy_status")

@mcp.tool()
def export_har(limit: int = 100):
    """导出HAR"""
    return call_proxypin_tool("export_har", {"limit": limit})

@mcp.tool()
def import_har(har_content: str):
    """导入HAR文件到ProxyPin
    
    参数:
    - har_content: HAR JSON字符串
    """
    return call_proxypin_tool("import_har", {"har_content": har_content})

@mcp.tool()
def start_proxy(port: int = 9099):
    """启动代理服务器
    
    参数:
    - port: 代理端口(默认9099)
    """
    return call_proxypin_tool("start_proxy", {"port": port})

@mcp.tool()
def stop_proxy():
    """停止代理服务器"""
    return call_proxypin_tool("stop_proxy")

@mcp.tool()
def get_recent_requests(limit: int = 20, url_filter: str = None, method: str = None):
    """获取最近的请求列表(Legacy)
    
    注意: 建议使用 search_requests 替代此方法
    """
    args = {"limit": limit}
    if url_filter:
        args["url_filter"] = url_filter
    if method:
        args["method"] = method
    return call_proxypin_tool("get_recent_requests", args)

@mcp.tool()
def clear_requests():
    """清空所有捕获的请求"""
    return call_proxypin_tool("clear_requests")

@mcp.tool()
def get_statistics():
    """获取请求统计信息
    
    返回：
    - total: 总请求数
    - methods: HTTP方法分布
    - statusCodes: 状态码分布(2xx/3xx/4xx/5xx)
    - domains: 域名分布
    - totalSize: 总数据大小
    - averageDuration: 平均响应时间
    - errorCount: 错误请求数
    """
    return call_proxypin_tool("get_statistics")

@mcp.tool()
def compare_requests(request_id_1: str, request_id_2: str):
    """对比两个请求的差异
    
    返回详细对比信息：
    - request_header_diff: 请求Header差异
    - response_header_diff: 响应Header差异
    - request_body_diff: 请求Body差异(支持JSON diff)
    - response_body_diff: 响应Body差异(支持JSON diff)
    - duration_diff: 响应时间差异
    """
    return call_proxypin_tool("compare_requests", {
        "request_id_1": request_id_1,
        "request_id_2": request_id_2
    })

@mcp.tool()
def find_similar_requests(request_id: str, limit: int = 10):
    """查找与指定请求相似的其他请求
    
    相似条件：相同域名、路径和HTTP方法
    """
    return call_proxypin_tool("find_similar_requests", {
        "request_id": request_id,
        "limit": limit
    })

@mcp.tool()
def extract_api_endpoints(domain_filter: str = None):
    """提取并分组所有API端点
    
    返回：
    - endpoints: 端点列表(包含method/domain/path/count/status_codes)
    - total_unique: 唯一端点总数
    
    用途：自动生成API文档、了解系统API结构
    """
    args = {}
    if domain_filter:
        args["domain_filter"] = domain_filter
    return call_proxypin_tool("extract_api_endpoints", args)

if __name__ == "__main__":
    mcp.run()
