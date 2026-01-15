import requests
import re
import sys
import os
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_real_url(share_text):
    url_pattern = re.compile(r'https?://v\.douyin\.com/[a-zA-Z0-9_-]+/')
    match = url_pattern.search(share_text)
    if not match:
        print("No URL found in text")
        return None
    return match.group(0)
    
def get_media_info(url, text):
    """Identify media type and ID from URL or page content."""
    # 1. Check for Note ID in URL
    note_match = re.search(r'/note/(\d+)', url)
    if note_match:
        return note_match.group(1), 'note'

    # 2. Check for Video ID in URL
    video_url_match = re.search(r'[?&]video_id=(\d+)', url)
    if video_url_match:
        return video_url_match.group(1), 'video'

    # 3. Check for Video ID in page content
    video_text_match = re.search(r'video_id=([a-zA-Z0-9]+)', text)
    if video_text_match:
        return video_text_match.group(1), 'video'

    return None, None

def get_page_response(session, url):
    """Get final page response, handling specific redirects."""
    response = session.get(url, allow_redirects=False, verify=False)
    
    if response.status_code in [301, 302]:
        long_url = response.headers.get('Location')
        if long_url:
            if '/slides/' in long_url:
                print(f"Replacing slides with note: {long_url}")
                long_url = long_url.replace('/slides/', '/note/')
            
            print(f"Redirected to: {long_url}")
            return session.get(long_url, verify=False)
            
    return response

def parse_img_list(body):
    content = body.replace(r'\u002F', '/').replace('/', '/')    
    
    # Match the url_list content to capture all links
    # First, try to locate the 'images' array to narrow down the scope
    images_content = content

    start_idx = content.find('"images":[')

    if start_idx != -1:
        # Simple bracket counting to extract the array content
        count = 1
        search_start = start_idx + 10 
        for i in range(search_start, len(content)):
            if content[i] == '[':
                count += 1
            elif content[i] == ']':
                count -= 1
            if count == 0:
                images_content = content[start_idx:i+1]
                break

    list_reg = re.compile(r'\{"uri":"[^\s"]+","url_list":\[([^\]]*)\]')

    lists = list_reg.findall(images_content)
    
    first_urls = []
    
    url_item_reg = re.compile(r'"(https://p\d{1,2}-sign\.douyinpic\.com/[^"]+)"')
    
    for l in lists:
        first_urls.extend(url_item_reg.findall(l))

    first_urls = [url for url in first_urls if "shrink" not in url]

    url_ret = re.compile(r'"uri":"([^\s"]+)","url_list":')
    
    uris = url_ret.findall(content)
    
    uri_set = set(uris)

    r_list = []

    for uri in uri_set:        
        for url in first_urls:
            if uri in url:
                r_list.append(url)
                break
    
    filtered_r_list = [url for url in r_list if "/obj/" not in url]
    
    return filtered_r_list

def download_img(session, img_list, img_id):
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for idx, img_url in enumerate(img_list):
        print(f"Downloading image {idx+1}/{len(img_list)}: {img_url}")
        try:
            img_resp = session.get(img_url, verify=False)
            if img_resp.status_code == 200:
                content_type = img_resp.headers.get('Content-Type', '')
                ext = '.jpeg'
                if 'webp' in content_type:
                    ext = '.webp'
                elif 'png' in content_type:
                    ext = '.png'
                    
                filename = os.path.join(output_dir, f"Img_{img_id}_{idx+1}{ext}")
                with open(filename, 'wb') as f:
                    f.write(img_resp.content)
                print(f"Saved to {filename}")
            else:
                print(f"Failed to download image {idx+1}. Status: {img_resp.status_code}")

        except Exception as e:
            print(f"Error downloading image {idx+1}: {e}")

def download_video(session, video_id):
    # 3. Construct API URL for no-watermark video
    # Using api.amemv.com as it seems more reliable for this
    # Use 1080p for higher quality
    api_url = f"https://api.amemv.com/aweme/v1/play/?video_id={video_id}&ratio=1080p&line=0"
    
    # 4. Get the real video location
    play_resp = session.get(api_url, allow_redirects=False, verify=False)
    print(f"API Response Status: {play_resp.status_code}")
    if play_resp.status_code not in [301, 302]:
        print(f"Failed to get video location. Status: {play_resp.status_code}")
        return
        
    real_video_url = play_resp.headers['Location']
    print(f"Downloading from: {real_video_url}")
    
    # 5. Download the video
    video_resp = session.get(real_video_url, verify=False, stream=True)
    
    # Setup output directory
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Extract filename from headers or generate one
    filename = os.path.join(output_dir, f"Video_{video_id}.mp4")
    
    total_size = int(video_resp.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    
    with open(filename, 'wb') as f:
        downloaded = 0
        for data in video_resp.iter_content(block_size):
            downloaded += len(data)
            f.write(data)
            # Simple progress bar
            if total_size > 0:
                percent = int(50 * downloaded / total_size)
                sys.stdout.write(f"\r[{'=' * percent}{' ' * (50 - percent)}] {downloaded}/{total_size} bytes")
                sys.stdout.flush()
    
    print(f"\nVideo saved to: {os.path.abspath(filename)}")

def download_fn(share_text):
    short_url = get_real_url(share_text)
    if not short_url:
        return

    print(f"Analyzing URL: {short_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        
        # 1. Get page content (handling redirects)
        page_resp = get_page_response(session, short_url)
        
        if page_resp.status_code != 200:
            print(f"Failed to retrieve page. Status: {page_resp.status_code}")
            return

        # 2. Identify media type and ID
        media_id, media_type = get_media_info(page_resp.url, page_resp.text)
        
        print(f"Found ID: {media_id}")
        print(f"Found Type: {media_type}")

        if media_type == 'note':
            img_list = parse_img_list(page_resp.text)
            print(f"Found {len(img_list)} images")
            if len(img_list) > 0:
                download_img(session, img_list, media_id)
        elif media_type == 'video':
            download_video(session, media_id)
        else:
            print("Could not find video ID or images.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = input("Please enter the share text or URL: ")
    
    download_fn(text)

