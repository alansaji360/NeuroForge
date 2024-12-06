/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "dac.h"
#include "dma.h"
#include "sdadc.h"
#include "tim.h"
#include "usb_device.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "usb_device.h"
#include "usbd_cdc_if.h"
#include "usbd_core.h"

#include "IIR.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
// # samples per data block(half buffer)
#define DATASIZE 128
// full buffer size
#define BUFFERSIZE DATASIZE * 2
#define CHANNELWIDTH 4

//USB CONSTANTS
#define DATA_POINTS_PER_PACKET 128
#define NUM_BUFFERS_TO_PACK 12
#define LIVE_READ_PACKET_SIZE ((DATA_POINTS_PER_PACKET + 2) * NUM_BUFFERS_TO_PACK)

uint16_t live_read_packet[LIVE_READ_PACKET_SIZE];
uint16_t live_read_packet_2[LIVE_READ_PACKET_SIZE];

uint16_t adc_vals[CHANNELWIDTH][BUFFERSIZE];
uint16_t alpha_vals[CHANNELWIDTH][BUFFERSIZE];
uint16_t beta_vals[CHANNELWIDTH][BUFFERSIZE];
uint16_t gamma_vals[CHANNELWIDTH][BUFFERSIZE];

uint16_t test[BUFFERSIZE];

uint16_t conv_val;

uint8_t ch;
uint8_t usb_start;

uint8_t half_full_usb[CHANNELWIDTH] = {0};
uint8_t full_usb[CHANNELWIDTH] = {0};

uint8_t ctr[CHANNELWIDTH] = {0};
uint8_t conv_ctr[CHANNELWIDTH] = {0};

uint8_t half_flag[CHANNELWIDTH] = {0};

uint8_t data_ready[CHANNELWIDTH] = {0};

__IO uint32_t InjChannel = 0;


static volatile uint16_t* input_buffer_ptr[CHANNELWIDTH] = {&adc_vals[0][0], &adc_vals[1][0], &adc_vals[2][0], &adc_vals[3][0]};

static volatile uint16_t* alpha_buffer_ptr[CHANNELWIDTH] = {&alpha_vals[0][0], &alpha_vals[1][0], &alpha_vals[2][0], &alpha_vals[3][0]};
static volatile uint16_t* beta_buffer_ptr[CHANNELWIDTH] = {&beta_vals[0][0], &beta_vals[1][0], &beta_vals[2][0], &beta_vals[3][0]};
static volatile uint16_t* gamma_buffer_ptr[CHANNELWIDTH] = {&gamma_vals[0][0], &gamma_vals[1][0], &gamma_vals[2][0], &gamma_vals[3][0]};

IIR1 high_8_1[CHANNELWIDTH], high_8_2[CHANNELWIDTH], high_8_3[CHANNELWIDTH];

IIR1 low_12_1[CHANNELWIDTH], low_12_2[CHANNELWIDTH], low_12_3[CHANNELWIDTH];

IIR2 high_12_1[CHANNELWIDTH], high_12_2[CHANNELWIDTH];

IIR2 low_30_1[CHANNELWIDTH], low_30_2[CHANNELWIDTH];

IIR2 high_30_1[CHANNELWIDTH], high_30_2[CHANNELWIDTH];

IIR2 low_100_1[CHANNELWIDTH], low_100_2[CHANNELWIDTH];


// TEMP VARIABLES
int num_packets_per_flag;
int half_repeated = 0;
int full_repeated = 0;
int half_entered = 0;
int full_entered = 0;
int last_half_sent = 0;
int usb_success = 0;
int usb_success_2 = 0;
int usb_busy = 0;
int usb_busy_2 = 0;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

void package_point(uint16_t* final_packet_buffer, uint16_t* unpacked_buffer, uint16_t identifier, int final_packet_pointer, int buffer_pointer, int num_points) {
    uint16_t zero = 0;
    final_packet_buffer[final_packet_pointer * (num_points + 2)] = zero;
    final_packet_buffer[final_packet_pointer * (num_points + 2) + 1] = identifier;
    for (int i = 0; i < num_points; i++) {
        final_packet_buffer[final_packet_pointer * (num_points + 2) + 2 + i] = unpacked_buffer[buffer_pointer + i];
    }
//    final_packet_buffer[final_packet_pointer * 3 + 2] = unpacked_buffer[buffer_pointer];

}
void package_several_points_per_buffer(uint16_t* final_packet_buffer, uint16_t** unpacked_buffers, int num_unpacked_buffers, int buffer_pointer, int num_points) {
    for(int i = 0; i < num_unpacked_buffers; i++) {
            package_point(final_packet_buffer, unpacked_buffers[i], (uint16_t) i, i, buffer_pointer, num_points);
    //        track++;
        }
}

void package_point_2(uint16_t* final_packet_buffer, uint16_t* unpacked_buffer, uint16_t identifier, int final_packet_pointer, int buffer_pointer, int num_points) {
    uint16_t zero = 0;
    final_packet_buffer[final_packet_pointer * (num_points + 2)] = zero;
    final_packet_buffer[final_packet_pointer * (num_points + 2) + 1] = identifier;
    for (int i = 0; i < num_points; i++) {
        final_packet_buffer[final_packet_pointer * (num_points + 2) + 2 + i] = unpacked_buffer[buffer_pointer + i + DATASIZE];
    }
//    final_packet_buffer[final_packet_pointer * 3 + 2] = unpacked_buffer[buffer_pointer];

}
void package_several_points_per_buffer_2(
        uint16_t* final_packet_buffer,
        uint16_t** unpacked_buffers,
        int num_unpacked_buffers,
        int buffer_pointer,
        int num_points) {
    for(int i = 0; i < num_unpacked_buffers; i++) {
            package_point_2(final_packet_buffer, unpacked_buffers[i], (uint16_t) i, i, buffer_pointer, num_points);
    //        track++;
        }
}

int aux_retrigger_usb()
{
//    GPIO_InitTypeDef GPIO_InitStructure;
//    USBD_Stop(&hUsbDeviceFS);
    HAL_Delay(100);
//    USBD_DeInit(&hUsbDeviceFS);

//    MX_USB_DEVICE_Init();

//    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_5, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_5, GPIO_PIN_SET);


    // Delay to ensure the host detects the disconnect
    HAL_Delay(500);
    MX_USB_DEVICE_Init();

//    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_5, GPIO_PIN_SET);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_5, GPIO_PIN_RESET);

    HAL_Delay(500);  // Small delay for stability

    // Initialize USB Device
//    MX_USB_DEVICE_Init();

    // Start the USB device
//    USBD_Start(&hUsbDeviceFS);
    return 1;
}

void DSP(uint8_t chl, uint8_t flag){

	float in8high;
	float out8high;

//	float in12low;
	float out12low;

	float in12high;
	float out12high;

//	float in30low;
	float out30low;

	float in30high;
	float out30high;

//	float in100low;
	float out100low;

	for(int i = 0; i < DATASIZE; i++){

		in8high = (float) (input_buffer_ptr[chl][i]);
//		in12low = (float) (input_buffer_ptr[chl][i]);
		in12high = (float) (input_buffer_ptr[chl][i]);
//		in30low = (float) (input_buffer_ptr[chl][i]);
		in30high = (float) (input_buffer_ptr[chl][i]);
//		in100low = (float) (input_buffer_ptr[chl][i]);

		out8high = IIR1_Update(&high_8_1[chl], in8high);
		out8high = IIR1_Update(&high_8_2[chl], out8high);
		out8high = IIR1_Update(&high_8_3[chl], out8high);

		out12low = IIR1_Update(&low_12_1[chl], out8high);
		out12low = IIR1_Update(&low_12_2[chl], out12low);
		out12low = IIR1_Update(&low_12_3[chl], out12low) + 20000;

		out12high = IIR2_Update(&high_12_1[chl], in12high);
		out12high = IIR2_Update(&high_12_2[chl], out12high);

		out30low = IIR2_Update(&low_30_1[chl], out12high);
		out30low = IIR2_Update(&low_30_2[chl], out30low) + 20000;

		out30high = IIR2_Update(&high_30_1[chl], in30high);
		out30high = IIR2_Update(&high_30_2[chl], out30high);

		out100low = IIR2_Update(&low_100_1[chl], out30high);
		out100low = IIR2_Update(&low_100_2[chl], out100low) + 20000;

		alpha_buffer_ptr[chl][i] = (uint16_t) (out12low);
		beta_buffer_ptr[chl][i] = (uint16_t) (out30low);
		gamma_buffer_ptr[chl][i] = (uint16_t) (out100low);

//		if(chl == 0){
//			alpha_buffer_ptr[chl][i] = input_buffer_ptr[chl][i];
//			beta_buffer_ptr[chl][i] = 0;
//			gamma_buffer_ptr[chl][i] = 0;
//		}
	}
	data_ready[chl] = 0;
	if(flag == 1){
		half_full_usb[chl] = 1;
	}
	else if (flag == 0){
		full_usb[chl] = 1;
	}

//	half_full_usb[2] = 1;
//	half_full_usb[3] = 1;
//	full_usb[2] = 1;
//	full_usb[3] = 1;
}

void Cycle_Delay(uint16_t cycles_to_wait){
  __disable_irq();

  // Start Timer 7
  HAL_TIM_Base_Start(&htim7);

  while (__HAL_TIM_GET_COUNTER(&htim7) < cycles_to_wait) {
  }

  // Stop Timer 7
  HAL_TIM_Base_Stop(&htim7);
  __HAL_TIM_SET_COUNTER(&htim7, 0);

  // Re-enable interrupts
  __enable_irq();
}

void HAL_SDADC_InjectedConvCpltCallback(SDADC_HandleTypeDef *hsdadc)
{
  conv_val = HAL_SDADC_InjectedGetValue(hsdadc, (uint32_t *) &InjChannel);
  if (hsdadc->Instance == SDADC1){
	  // SDADC1 completed the injected conversion
	  if(InjChannel == 2){
		  ch = 0;
	  }
	  else if(InjChannel == 4){
		  ch = 1;
	  }
	  else if(InjChannel == 1){
		  ch = 2;
	  }
	  else if(InjChannel == 6){
		  ch = 3;
	  }
  }
//  else if (hsdadc->Instance == SDADC2){
//	  // SDADC2 completed the injected conversion
//	  if(InjChannel == 2){
//		  ch = 2;
//	  }
//	  else if(InjChannel == 1){
//		  ch = 3;
//	  }
//  }

  HAL_DAC_SetValue(&hdac2, DAC_CHANNEL_1, DAC_ALIGN_12B_R, gamma_vals[0][conv_ctr[0]]);


  adc_vals[ch][conv_ctr[ch]] = conv_val;

  if((ctr[ch] == DATASIZE - 1)){
	  if(half_flag[ch] == 0){ // first half filled
		  input_buffer_ptr[ch] = &adc_vals[ch][0];

		  alpha_buffer_ptr[ch] = &alpha_vals[ch][0];
		  beta_buffer_ptr[ch] = &beta_vals[ch][0];
		  gamma_buffer_ptr[ch] = &gamma_vals[ch][0];

		  half_flag[ch] = 1;
	  }
	  else if(half_flag[ch] == 1){ //second half filled
		  input_buffer_ptr[ch] = &adc_vals[ch][DATASIZE];

		  alpha_buffer_ptr[ch] = &alpha_vals[ch][DATASIZE];
		  beta_buffer_ptr[ch] = &beta_vals[ch][DATASIZE];
		  gamma_buffer_ptr[ch] = &gamma_vals[ch][DATASIZE];

		  half_flag[ch] = 0;
	  }
	  data_ready[ch] = 1;
  }

  ctr[ch] = (ctr[ch] == DATASIZE - 1) ? 0 : ctr[ch] + 1;
  conv_ctr[ch] = (conv_ctr[ch] == BUFFERSIZE - 1) ? 0 : conv_ctr[ch] + 1;
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
  usb_start = 1;

  __disable_irq();

  // Start Timer 7
  HAL_TIM_Base_Start(&htim7);

  while (__HAL_TIM_GET_COUNTER(&htim7) < 65534) {
  }

  // Stop Timer 7
  HAL_TIM_Base_Stop(&htim7);
  __HAL_TIM_SET_COUNTER(&htim7, 0);

  // Re-enable interrupts
  __enable_irq();
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
  __disable_irq();

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_DAC2_Init();
  MX_SDADC1_Init();
  MX_TIM6_Init();
  MX_TIM13_Init();
  MX_USB_DEVICE_Init();
  MX_TIM17_Init();
  MX_SDADC2_Init();
  MX_TIM7_Init();
  MX_TIM19_Init();
  /* USER CODE BEGIN 2 */
  __enable_irq();
//  aux_retrigger_usb();

  // INIT FILTERS
//  for(int i = 0; i < CHANNELWIDTH; i++){
//	// 8 Hz High
//	IIR1_Init(&high_8_1[i], -0.9980, 0.9990, -0.9990);
//	IIR1_Init(&high_8_2[i], -0.9980, 0.9990, -0.9990);
//	IIR1_Init(&high_8_3[i], -0.9980, 0.9990, -0.9990);
//
//	// 12 Hz low
//	IIR1_Init(&low_12_1[i], -0.9898, 0.0051, 0.0051);
//	IIR1_Init(&low_12_2[i], -0.9837, 0.0082, 0.0082);
//	IIR1_Init(&low_12_3[i], -0.9871, 0.0065, 0.0065);
//
//	// 12 Hz High
//	IIR2_Init(&high_12_1[i], -1.9947, 0.9947, 0.9096, -1.8192, 0.9096);
//	IIR2_Init(&high_12_2[i], -1.9901, 0.9902, 0.9951, -1.9902, 0.9951);
//
//	// 30 Hz low
//	IIR2_Init(&low_30_1[i], -1.9828, 0.9835, 0.5578, -1.1149, 0.5578);
//	IIR2_Init(&low_30_2[i], -1.9770, 0.9777, 0.3128, -0.6249, 0.3128);
//
//	// 30 Hz High
//	IIR2_Init(&high_30_1[i], -1.9744, 0.9748, 0.9429, -1.8857, 0.9429);
//	IIR2_Init(&high_30_2[i], -1.9711, 0.9717, 0.9413, -1.8827, 0.9413);
//
//	// 100 Hz Low
//	IIR2_Init(&low_100_1[i], -1.974264, 0.975777, 0.555675, -1.109922, 0.555675);
//	IIR2_Init(&low_100_2[i], -1.966697, 0.969158, 0.553904, -1.105485, 0.553904);
//
//  }
  for(int i = 0; i < CHANNELWIDTH; i++){ // filters for signals sampled by sdadc2
	// 8 Hz High
	IIR1_Init(&high_8_1[i], -0.995746, 0.997873, -0.997873);
	IIR1_Init(&high_8_2[i], -0.994156, 0.997078, -0.997078);
	IIR1_Init(&high_8_3[i], -0.995039, 0.997519, -0.997519);

	// 12 Hz low
	IIR1_Init(&low_12_1[i], -0.972264, 0.013868, 0.013868);
	IIR1_Init(&low_12_2[i], -0.966278, 0.016861, 0.016861);
	IIR1_Init(&low_12_3[i], -0.969599, 0.015201, 0.015201);

	// 12 Hz High
	IIR2_Init(&high_12_1[i], -1.981415, 0.981780, 0.883059, -1.766082, 0.883059);
	IIR2_Init(&high_12_2[i], -1.977786, 0.978031, 0.988954, -1.977908, 0.988954);

	// 30 Hz low
	IIR2_Init(&low_30_1[i], -1.966084, 0.968630, 0.553764, -1.105124, 0.553764);
	IIR2_Init(&low_30_2[i], -1.956684, 0.959172, 0.310149, -0.618004, 0.310149);

	// 30 Hz High
	IIR2_Init(&high_30_1[i], -1.950197, 0.951961, 0.920969, -1.841937, 0.920969);
	IIR2_Init(&high_30_2[i], -1.944739, 0.947082, 0.897621, -1.795241, 0.897621);

	// 100 Hz Low
	IIR2_Init(&low_100_1[i], -1.938012, 0.945733, 0.547820, -1.088351, 0.547820);
	IIR2_Init(&low_100_2[i], -1.929655, 0.939339, 0.546209, -1.083277, 0.546209);

  }

  HAL_SDADC_CalibrationStart(&hsdadc1, SDADC_CALIBRATION_SEQ_1);
  HAL_SDADC_PollForCalibEvent(&hsdadc1, 10);

  HAL_SDADC_CalibrationStart(&hsdadc2, SDADC_CALIBRATION_SEQ_1);
  HAL_SDADC_PollForCalibEvent(&hsdadc2, 10);


  HAL_TIM_Base_Start(&htim6);
  HAL_TIM_PWM_Start(&htim13, TIM_CHANNEL_1);
  HAL_TIM_PWM_Start(&htim17, TIM_CHANNEL_1);
  HAL_SDADC_InjectedStart_IT(&hsdadc1);
//  HAL_SDADC_InjectedStart_IT(&hsdadc2);
  HAL_DAC_Start(&hdac2, DAC_CHANNEL_1);
  usb_start = 0;
  uint16_t* usb_buffers[] = {
		alpha_vals[0],
		beta_vals[0],
		gamma_vals[0],
		alpha_vals[1],
		beta_vals[1],
		gamma_vals[1],
	    alpha_vals[2],
	    beta_vals[2],
	    gamma_vals[2],
		alpha_vals[3],
		beta_vals[3],
		gamma_vals[3]
	};

//  aux_retrigger_usb();
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  if(data_ready[0]){
		  DSP(0, half_flag[0]);
	  }
	  if(data_ready[1]){
		  DSP(1, half_flag[1]);
	  }
	  if(data_ready[2]){
		  DSP(2, half_flag[2]);
	  }
	  if(data_ready[3]){
		  DSP(3, half_flag[3]);
	  }

	  if(usb_start){
//		  if(half_full_usb[0] == 1 && half_full_usb[1] == 1 && half_full_usb[2] == 1 && half_full_usb[3] == 1 && last_half_sent == 2) {
//
//			half_full_usb[0] = 0;
//			half_full_usb[1] = 0;
//			half_full_usb[2] = 0;
//			half_full_usb[3] = 0;
//			int buffer_index_counter = 0;
//			int num_loops = 0;
//
//			for(int i = 0; i < DATASIZE; i += DATA_POINTS_PER_PACKET) {
////			  start_time = HAL_GetTick();
//			  package_several_points_per_buffer(live_read_packet, usb_buffers, NUM_BUFFERS_TO_PACK, buffer_index_counter, DATA_POINTS_PER_PACKET);
//			  buffer_index_counter += DATA_POINTS_PER_PACKET;
//			  CDC_Transmit_FS((uint8_t*)&live_read_packet, sizeof(live_read_packet));
//			  num_loops++;
//			  if (num_loops > num_packets_per_flag) {
//				  num_packets_per_flag = num_loops;
//			  }
//			}
//			last_half_sent = 1;
//		  }
//		  if(full_usb[0] == 1 && full_usb[1] == 1 && full_usb[2] == 1 && full_usb[3] == 1 && last_half_sent == 1) {
//
//			full_usb[0] = 0;
//			full_usb[1] = 0;
//			full_usb[2] = 0;
//			full_usb[3] = 0;
//			int buffer_index_counter = DATASIZE;
//
//			for(int i = 0; i < DATASIZE; i += DATA_POINTS_PER_PACKET) {
//			  package_several_points_per_buffer(live_read_packet_2, usb_buffers, NUM_BUFFERS_TO_PACK, buffer_index_counter, DATA_POINTS_PER_PACKET);
//			  buffer_index_counter += DATA_POINTS_PER_PACKET;
//			  CDC_Transmit_FS((uint8_t*)&live_read_packet_2, sizeof(live_read_packet_2));
//		    }
//			last_half_sent = 2;
//		  }
		  if(half_full_usb[0] == 1 && half_full_usb[1] == 1 && half_full_usb[2] == 1 && half_full_usb[3] == 1) {
			  	  	if (last_half_sent == 1) {
			  	  		half_repeated++;
			  	  	}
			  	  	half_entered++;


		  			half_full_usb[0] = 0;
		  			half_full_usb[1] = 0;
		  			half_full_usb[2] = 0;
		  			half_full_usb[3] = 0;
		  			int buffer_index_counter = 0;
		  			int num_loops = 0;

		  			for(int i = 0; i < DATASIZE; i += DATA_POINTS_PER_PACKET) {
		  //			  start_time = HAL_GetTick();
		  			  package_several_points_per_buffer(live_read_packet, usb_buffers, NUM_BUFFERS_TO_PACK, buffer_index_counter, DATA_POINTS_PER_PACKET);
		  			  buffer_index_counter += DATA_POINTS_PER_PACKET;
		  			  int result = CDC_Transmit_FS((uint8_t*)&live_read_packet, sizeof(live_read_packet));
		  			  if(result == 0) {
		  				  usb_success++;
		  			  } else if(result == 1) {
		  				  usb_busy++;
		  			  }
		  			  num_loops++;
		  			  if (num_loops > num_packets_per_flag) {
		  				  num_packets_per_flag = num_loops;
		  			  }
		  			}
		  			last_half_sent = 1;
		  		  }
		  		  if(full_usb[0] == 1 && full_usb[1] == 1 && full_usb[2] == 1 && full_usb[3] == 1) {
		  			full_entered++;
		  			full_usb[0] = 0;
		  			full_usb[1] = 0;
		  			full_usb[2] = 0;
		  			full_usb[3] = 0;
		  			if (last_half_sent == 2) {
		  				full_repeated++;
		  			}
		  			int buffer_index_counter = DATASIZE;

		  			for(int i = 0; i < DATASIZE; i += DATA_POINTS_PER_PACKET) {
		  			  package_several_points_per_buffer(live_read_packet_2, usb_buffers, NUM_BUFFERS_TO_PACK, buffer_index_counter, DATA_POINTS_PER_PACKET);
		  			  buffer_index_counter += DATA_POINTS_PER_PACKET;
		  			  int result = CDC_Transmit_FS((uint8_t*)&live_read_packet_2, sizeof(live_read_packet_2));
		  			  if(result == 0) {
		  				  usb_success_2++;
					  } else if(result == 1) {
						  usb_busy_2++;
					  }

		  		    }
		  			last_half_sent = 2;
		  		  }
      }

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */


  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_USB|RCC_PERIPHCLK_SDADC;
  PeriphClkInit.USBClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5;
  PeriphClkInit.SdadcClockSelection = RCC_SDADCSYSCLK_DIV12;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
  HAL_PWREx_EnableSDADC(PWR_SDADC_ANALOG1);
  HAL_PWREx_EnableSDADC(PWR_SDADC_ANALOG2);
}

/* USER CODE BEGIN 4 */


/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
