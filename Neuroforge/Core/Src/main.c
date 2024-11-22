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

uint16_t adc_vals[CHANNELWIDTH][BUFFERSIZE];
uint16_t dac_vals[CHANNELWIDTH][BUFFERSIZE];

uint16_t conv_val;

uint8_t ch;
uint8_t ch_out = 0;

uint8_t half_full_usb[CHANNELWIDTH] = {0};
uint8_t full_usb[CHANNELWIDTH] = {0};

uint8_t ctr[CHANNELWIDTH] = {0};
uint8_t conv_ctr[CHANNELWIDTH] = {0};

uint8_t half_flag[CHANNELWIDTH] = {0};

uint8_t data_ready[CHANNELWIDTH] = {0};

__IO uint32_t InjChannel = 0;

static volatile uint16_t* input_buffer_ptr[CHANNELWIDTH] = {&adc_vals[0][0], &adc_vals[1][0], &adc_vals[2][0], &adc_vals[3][0]};
static volatile uint16_t* output_buffer_ptr[CHANNELWIDTH] = {&dac_vals[0][0], &dac_vals[1][0], &dac_vals[2][0], &dac_vals[3][0]};

IIR1 high_8_1[CHANNELWIDTH], high_8_2[CHANNELWIDTH], high_8_3[CHANNELWIDTH];

IIR1 low_12_1[CHANNELWIDTH], low_12_2[CHANNELWIDTH], low_12_3[CHANNELWIDTH];

IIR2 high_12_1[CHANNELWIDTH], high_12_2[CHANNELWIDTH];

IIR2 low_30_1[CHANNELWIDTH], low_30_2[CHANNELWIDTH];

IIR2 high_30_1[CHANNELWIDTH], high_30_2[CHANNELWIDTH];

IIR2 low_100_1[CHANNELWIDTH], low_100_2[CHANNELWIDTH];

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

void DSP(uint8_t chl){

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
//		in8high = (float) (input_buffer_ptr[chl][i]);
////		in12low = (float) (input_buffer_ptr[i]);
//		in12high = (float) (input_buffer_ptr[chl][i]);
////		in30low = (float) (input_buffer_ptr[i]);
//		in30high = (float) (input_buffer_ptr[chl][i]);
////		in100low = (float) (input_buffer_ptr[i]);
//
//		out8high = IIR1_Update(&high_8_1[chl], in8high);
//		out8high = IIR1_Update(&high_8_2[chl], out8high);
//		out8high = IIR1_Update(&high_8_3[chl], out8high) + 1500;
//
//		out12low = IIR1_Update(&low_12_1[chl], out8high);
//		out12low = IIR1_Update(&low_12_2[chl], out12low);
//		out12low = IIR1_Update(&low_12_3[chl], out12low);
//		out12low *= 1.5;
//
//		out12high = IIR2_Update(&high_12_1[chl], in12high);
//		out12high = IIR2_Update(&high_12_2[chl], out12high) + 1500;
//		out12high *= 1.1;
//
//		out30low = IIR2_Update(&low_30_1[chl], out12high);
//		out30low = IIR2_Update(&low_30_2[chl], out30low) + 14000;
//
//		out30high = IIR2_Update(&high_30_1[chl], in30high);
//		out30high = IIR2_Update(&high_30_2[chl], out30high);
//
//		out100low = IIR2_Update(&low_100_1[chl], out30high);
//		out100low = IIR2_Update(&low_100_2[chl], out100low) * 1;
//
//		output_buffer_ptr[chl][i] = ((uint16_t) (out30low)) >> 4;
		output_buffer_ptr[chl][i] = input_buffer_ptr[chl][i] >> 4;

//		alpha_buffer_ptr[i] = (uint32_t) (out12low);
//		beta_buffer_ptr[i] = (uint32_t) (out30low);
//		gamma_buffer_ptr[i] = (uint32_t) (out100low);
	}
	data_ready[chl] = 0;
}

void DAC_Set(uint8_t chl){
	if(ch_out == 0 && chl == 0){
		HAL_DAC_SetValue(&hdac2, DAC_CHANNEL_1, DAC_ALIGN_12B_R, dac_vals[0][conv_ctr[0]]);
	}
	else if(ch_out == 1 && chl == 1){
		HAL_DAC_SetValue(&hdac2, DAC_CHANNEL_1, DAC_ALIGN_12B_R, dac_vals[1][conv_ctr[1]]);
	}
	else if(ch_out == 2 && chl == 2){
		HAL_DAC_SetValue(&hdac2, DAC_CHANNEL_1, DAC_ALIGN_12B_R, dac_vals[2][conv_ctr[2]]);
	}
	else if(ch_out == 3 && chl == 3){
		HAL_DAC_SetValue(&hdac2, DAC_CHANNEL_1, DAC_ALIGN_12B_R, dac_vals[3][conv_ctr[3]]);
	}
}

void HAL_SDADC_InjectedConvCpltCallback(SDADC_HandleTypeDef *hsdadc)
{
  conv_val = HAL_SDADC_InjectedGetValue(hsdadc, (uint32_t *) &InjChannel);
  if (hsdadc->Instance == SDADC1){
	  // SDADC1 completed the injected conversion
	  if(InjChannel == 2){
		  ch = 0;
	  }
	  else if(InjChannel == 8){
		  ch = 1;
	  }
  }
  else if (hsdadc->Instance == SDADC2){
	  // SDADC2 completed the injected conversion
	  if(InjChannel == 2){
		  ch = 2;
	  }
	  else if(InjChannel == 0){
		  ch = 3;
	  }
  }

  adc_vals[ch][conv_ctr[ch]] = conv_val;
  DAC_Set(ch);

  if((ctr[ch] == DATASIZE - 1)){
	  if(half_flag[ch] == 0){ // first half filled
		  input_buffer_ptr[ch] = &adc_vals[ch][0];
		  output_buffer_ptr[ch] = &dac_vals[ch][0];
		  half_full_usb[ch] = 1;
		  half_flag[ch] = 1;
	  }
	  else if(half_flag[ch] == 1){ //second half filled
		  input_buffer_ptr[ch] = &adc_vals[ch][DATASIZE];
		  output_buffer_ptr[ch] = &dac_vals[ch][DATASIZE];
		  full_usb[ch] = 1;
		  half_flag[ch] = 0;
	  }
	  data_ready[ch] = 1;
  }

  ctr[ch] = (ctr[ch] == DATASIZE - 1) ? 0 : ctr[ch] + 1;
  conv_ctr[ch] = (conv_ctr[ch] == BUFFERSIZE - 1) ? 0 : conv_ctr[ch] + 1;
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
  ch_out = (ch_out == 3) ? 0 : ch_out + 1;
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
  /* USER CODE BEGIN 2 */

  // INIT FILTERS
  for(int i = 0; i < CHANNELWIDTH; i++){
	// 8 Hz High
	IIR1_Init(&high_8_1[i], -0.9986, 0.9993, -0.9993);
	IIR1_Init(&high_8_2[i], -0.9986, 0.9993, -0.9993);
	IIR1_Init(&high_8_3[i], -0.9986, 0.9993, -0.9993);

	// 12 Hz low
	IIR1_Init(&low_12_1[i], -0.9925, 0.0038, 0.0038);
	IIR1_Init(&low_12_2[i], -0.9864, 0.0068, 0.0068);
	IIR1_Init(&low_12_3[i], -0.9898, 0.0051, 0.0051);

	// 12 Hz High
	IIR2_Init(&high_12_1[i], -1.9961, 0.9961, 0.9422, -1.8844, 0.9422);
	IIR2_Init(&high_12_2[i], -1.9990, 0.9990, 0.9221, -1.8442, 0.9221);

	// 30 Hz low
	IIR2_Init(&low_30_1[i], -1.9917, 0.9919, 0.5601, -1.1200, 0.5601);
	IIR2_Init(&low_30_2[i], -1.9879, 0.9881, 0.3144, -0.6286, 0.3144);

	// 30 Hz High
	IIR2_Init(&high_30_1[i], -1.9901, 0.9902, 0.9394, -1.8788, 0.9394);
	IIR2_Init(&high_30_2[i], -1.9863, 0.9865, 0.9163, -1.8326, 0.9163);

	// 100 Hz Low
	IIR2_Init(&low_100_1[i], -1.9626, 0.9645, 0.4390, -0.8762, 0.4390);
	IIR2_Init(&low_100_2[i], -1.9804, 0.9824, 0.9145, -1.8270, 0.9145);
  }

  HAL_SDADC_CalibrationStart(&hsdadc1, SDADC_CALIBRATION_SEQ_1);
  HAL_SDADC_PollForCalibEvent(&hsdadc1, 10);

  HAL_SDADC_CalibrationStart(&hsdadc2, SDADC_CALIBRATION_SEQ_1);
  HAL_SDADC_PollForCalibEvent(&hsdadc2, 10);

  HAL_TIM_Base_Start(&htim6);
  HAL_TIM_PWM_Start(&htim13, TIM_CHANNEL_1);
  HAL_TIM_PWM_Start(&htim17, TIM_CHANNEL_1);
  HAL_SDADC_InjectedStart_IT(&hsdadc1);
  HAL_SDADC_InjectedStart_IT(&hsdadc2);
  HAL_DAC_Start(&hdac2, DAC_CHANNEL_1);
  ch_out = 0;

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  if(data_ready[0]){
		  DSP(0);
	  }
	  if(data_ready[1]){
		  DSP(1);
	  }
	  if(data_ready[2]){
		  DSP(2);
	  }
	  if(data_ready[3]){
		  DSP(3);
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
