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
#include "comp.h"
#include "dac.h"
#include "dma.h"
#include "hdmi_cec.h"
#include "i2c.h"
#include "i2s.h"
#include "sdadc.h"
#include "spi.h"
#include "tim.h"
#include "tsc.h"
#include "usart.h"
#include "usb.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

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

uint16_t adc_vals[BUFFERSIZE];
uint16_t dac_vals[BUFFERSIZE];

uint32_t adc_val;
uint32_t dac_val;
uint16_t test;
uint8_t ctr = 0;
uint8_t start_pt_i = 0;
uint8_t start_pt_o = DATASIZE;
uint8_t half_flag = 0;

uint8_t data_ready;

__IO uint32_t InjChannel = 0;

static volatile uint16_t* input_buffer_ptr = &adc_vals[0];
static volatile uint16_t* output_buffer_ptr;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
//void HAL_SDADC_InjectedConvHalfCpltCallback(SDADC_HandleTypeDef* hsdadc)
//{
//	input_buffer_ptr = &adc_vals[DATASIZE];
//	output_buffer_ptr = &dac_vals[0];
//
//	data_ready = 1;
//}

//void HAL_SDADC_InjectedConvCpltCallback(SDADC_HandleTypeDef* hsdadc)
//{
//	input_buffer_ptr = &adc_vals[0];
//	output_buffer_ptr = &dac_vals[DATASIZE];
//
//	data_ready = 1;
//}

void HAL_SDADC_InjectedConvCpltCallback(SDADC_HandleTypeDef *hsdadc)
{
  /* Get conversion value */
  input_buffer_ptr[ctr] = HAL_SDADC_InjectedGetValue(hsdadc, (uint32_t *) &InjChannel);
  output_buffer_ptr[ctr] = input_buffer_ptr[ctr] >> 4;
  HAL_DAC_SetValue(&hdac2, DAC_CHANNEL_1, DAC_ALIGN_12B_R, output_buffer_ptr[ctr]);

  if(ctr == DATASIZE - 1){
	  if(half_flag == 0){
		  input_buffer_ptr = &adc_vals[DATASIZE];
		  output_buffer_ptr = &dac_vals[0];
	  }
	  else{
		  input_buffer_ptr = &adc_vals[0];
		  output_buffer_ptr = &dac_vals[DATASIZE];
	  }
	  data_ready = 1;
	  half_flag = !half_flag;
  }
  ctr = (ctr == DATASIZE - 1) ? 0 : ctr + 1;

}

void DSP(){
	for(int i = 0; i < DATASIZE; i++){
//		output_buffer_ptr[i] = input_buffer_ptr[i] >> 4;
//		dac_vals[i] = adc_vals[i];
//		HAL_Delay(1);
//		output_buffer_ptr[i] = ((input_buffer_ptr[i] & 0xfdfffff) >> 4) - 2097152;
	}
	data_ready = 0;
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
  MX_COMP2_Init();
  MX_HDMI_CEC_Init();
  MX_I2C1_Init();
  MX_I2C2_SMBUS_Init();
  MX_I2S1_Init();
  MX_SPI3_Init();
  MX_TSC_Init();
  MX_USART2_UART_Init();
  MX_USB_PCD_Init();
  MX_DAC2_Init();
  MX_SDADC1_Init();
  MX_TIM6_Init();
  MX_SDADC2_Init();
  MX_TIM13_Init();
  /* USER CODE BEGIN 2 */
  HAL_SDADC_CalibrationStart(&hsdadc1, SDADC_CALIBRATION_SEQ_1);
  HAL_SDADC_PollForCalibEvent(&hsdadc1, 10);
  HAL_TIM_Base_Start(&htim6);
  HAL_TIM_PWM_Start(&htim13, TIM_CHANNEL_1);
//  HAL_SDADC_InjectedStart_DMA(&hsdadc1, (uint32_t *) adc_vals, BUFFERSIZE);
//  HAL_DAC_Start_DMA(&hdac2, DAC_CHANNEL_1, (uint32_t *) dac_vals, BUFFERSIZE, DAC_ALIGN_12B_R);
  HAL_SDADC_InjectedStart_IT(&hsdadc1);
  HAL_DAC_Start(&hdac2, DAC_CHANNEL_1);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  if(data_ready){
		  DSP();
	  }
//	  dac_val = test >> 4;
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
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
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
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_USB|RCC_PERIPHCLK_USART2
                              |RCC_PERIPHCLK_CEC|RCC_PERIPHCLK_I2C1
                              |RCC_PERIPHCLK_I2C2|RCC_PERIPHCLK_SDADC;
  PeriphClkInit.Usart2ClockSelection = RCC_USART2CLKSOURCE_PCLK1;
  PeriphClkInit.I2c1ClockSelection = RCC_I2C1CLKSOURCE_HSI;
  PeriphClkInit.I2c2ClockSelection = RCC_I2C2CLKSOURCE_HSI;
  PeriphClkInit.USBClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5;
  PeriphClkInit.CecClockSelection = RCC_CECCLKSOURCE_HSI;
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
