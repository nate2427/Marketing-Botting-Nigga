import requests
import os, sys, time, json
from dotenv import load_dotenv
load_dotenv()

# global constants used in each function
COURSE_VIDEOS_DIR = '/Volumes/Courses/Build a Better Brain'
ASSEMBLY_AI_API_KEY = os.getenv('ASSEMBLY_AI_API_KEY')
UPLOAD_ENDPOINT = 'https://api.assemblyai.com/v2/upload'
TRANSCRIPT_ENDPOINT = "https://api.assemblyai.com/v2/transcript"
# headers for the request to AssemblyAI
HEADERS = {
            'authorization': ASSEMBLY_AI_API_KEY,
            'content-type': 'application/json'
          }
TEST_VIDEO_FILE = '/Volumes/Courses/Build a Better Brain/001. Introduction/01. Course Overview.mp4'

# read in the video chunk by chunk 
def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as f:
        start = time.time()
        while True:
            data = f.read(chunk_size)
            if not data:
                print('Status: Completed Uploading {} to AssemblyAI'.format(filename.split('/')[-1]))
                break
            # check if 2 seconds have passed
            if time.time() - start == 2:
                # if so, print the status of the process is uploading video
                print('Status: Uploading {} to AssemblyAI'.format(filename.split('/')[-1]))
                # reset the timer
                start = time.time()
            yield data

# upload the video to Assembly
def upload_video_file(filename):
    # submit requests with the data being the content from the video file
    response = requests.post(UPLOAD_ENDPOINT,
                            headers=HEADERS,
                            data=read_file(filename))
    # get the url to the location of the video that was just uploaded
    video_url = response.json()['upload_url'] # this is where the video file was uploaded
    return video_url

# summarize the video chapters using AssemblyAI
def summarize_video_chapters(video_url):
    # make a request to the transcipt endpoint with the video_url as the audio url
    response = requests.post(TRANSCRIPT_ENDPOINT,
                             headers=HEADERS,
                             json={
                                 "audio_url": video_url,
                                 "auto_chapters": True # this key:value pair tells AssemblyAI to generate chapter summaries
                             })
    # get the id of the transcription
    summary_id = response.json()['id']
    return summary_id

# checks to see when the transcript has been generated and then returns the video chapter summaries
def wait_for_summaries_to_generate(summary_id, video_filename):
    # create endpoint url to check if video transcript is done
    polling_endpoint =  os.path.join(TRANSCRIPT_ENDPOINT, summary_id)
    # check the status of the transcript
    status = ''
    response_result = None
    while status != 'completed':
        # call the polling endpoint
        response_result = requests.get(
            polling_endpoint,
            headers=HEADERS
        )
        # get the status
        status = response_result.json()['status']
        print('Status: {} {}'.format(status, video_filename))
        # if status is error, exit the bot and print message
        if status == 'error':
            sys.exit('\nVIDEO FILE FAILED TO PROCESS!!!\n')
        # if the file aint ready, sleep the bot for 10 seconds
        elif status != 'completed':
            time.sleep(10)
    # once summaries are generated, return the video chapter summaries
    if status == 'completed':
        return response_result.json()['chapters']

# saves the video chapter summaries to a new json file
def save_chapters(chapters, video_filename):
    # create filename to save the json into
    filename = video_filename + '_chapters.json'
    with open(filename, 'w') as f:
        # save the json
        json.dump(chapters, f, indent=4)
    print("\nSummary generated for {}!\n".format(video_filename))

# save the summaries created for each chapter of the video
def save_video_summaries(summary_id, video_filename):
    chapters = wait_for_summaries_to_generate(summary_id, video_filename)
    save_chapters(chapters, video_filename)

# generates chapter summaries for a video
def generate_video_summary(video_filename):
    # call upload video file
    video_url = upload_video_file(video_filename)
    # summarize the video file
    summary_id = summarize_video_chapters(video_url)
    # save the chapter summaries of the video
    save_video_summaries(summary_id, video_filename.split('/')[-1])

# creates chapter summaries for all videos in a course directory
def generate_summaries_for_course_videos():
    # get the course title from the course dir
    course_title = COURSE_VIDEOS_DIR.split('/')[-1]
    print('\n### Operation Generate Video Chapter Summaries for {} has commenced ###\n'.format(course_title))

    # create a folder to hold the video chapter summaries for each module
    summaries_directory_name = '_'.join(course_title.split()) + '_course_summaries'
    # make sure folder doesnt exist first
    if summaries_directory_name not in os.listdir():
        os.mkdir(summaries_directory_name)
        print('Directory {} created to hold the AI generated video chapter summaries'.format(summaries_directory_name))
    # if it does, notify skipping step
    else:
        print('Directory {} already exists to hold the AI generated video chapter summaries\nSkip folder creation step...\nContining...'.format(summaries_directory_name))

    # get a list of the course modules in module order
    course_modules = os.listdir(COURSE_VIDEOS_DIR)
    course_modules.sort()
    # loop through the modules
    for module in course_modules:
        # ignoring the .DS_Store files
        if module == '.DS_Store':
            continue
        # for each module, create a folder in the videos chapters summaries directory
        print('\nCreating directory \"{}\" inside directory {}:'.format(module, summaries_directory_name))
        module_videos_summaries_dir = os.path.join(summaries_directory_name, '_'.join(module.split()) + '_videos_summaries' )
        os.mkdir(module_videos_summaries_dir)
        # switch into the newly created directory that will hold the videos summaries for the current module
        os.chdir(module_videos_summaries_dir)
        # get the videos for each of the modules in video order
        module_dir = os.path.join( COURSE_VIDEOS_DIR ,module)
        module_videos = os.listdir(module_dir)
        module_videos.sort()
        # generate video chapter summaries for each video in the directory
        for video in module_videos:
            video_filename = os.path.join(COURSE_VIDEOS_DIR, module, video)
            generate_video_summary(video_filename)
        # print completed message to logger
        print('Completed summarizing the videos in module {}\nMoving on to the next module...'.format(module))
        # cd back to main directory of the program
        os.chdir('../../')

# tests a single video file to make sure the flow works
def test_video_summarize_flow():
    # call upload video file
    video_url = upload_video_file(TEST_VIDEO_FILE)
    # summarize the video file
    summary_id = summarize_video_chapters(video_url)
    # save the chapter summaries of the video
    save_video_summaries(summary_id)


if __name__ == '__main__':
    # make sure the flow works before doing it for all in the directory
    # test_video_summarize_flow()
    
    # opening statement
    print('\nStarting the Summarizing Course Module Botting Nigga\nWill let you know when its job has completed.')
    print('\nPrinting output to logfile\nWill complete soon...')
    orig_stdout = sys.stdout

    # redirect stdout (print statements) to a logfile
    log = open('summary_bot.log', 'a')
    sys.stdout = log

    print('\n############################# STARTS NEW LOG RUN #############################\n')

    # run the bot
    generate_summaries_for_course_videos()

    # reset stdout to its original location (the terminal)
    sys.stdout = orig_stdout
    print('\nThe Summarizing Course Module Botting Nigga has completed its job, sir\nDueces!!!\n')